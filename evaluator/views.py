# evaluator/views.py
import threading
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from decouple import config

from .models import Job
from .serializer import UploadSerializer, JobResultSerializer
from .utils import read_uploaded_file_text
from .llm import call_openrouter_chat
from .validate import validate_evaluation_result


SYSTEM_INSTRUCTION = (
    "You are an expert backend hiring evaluator. "
    "YOU MUST RETURN ONLY A VALID JSON OBJECT and nothing else."
)


def build_prompt(job_desc, cv_text, report_text, rubric):
    """
    Build the prompt that will be sent to the LLM.
    """
    return f"""
JOB_DESCRIPTION:
{job_desc}

CANDIDATE_CV:
{cv_text[:4000]}

PROJECT_REPORT:
{report_text[:8000]}

SCORING_RUBRIC:
{rubric}

Return ONLY a JSON object with keys:
- cv_match_rate: float between 0 and 1
- cv_feedback: short string
- project_scores: {{correctness:1-5, code_quality:1-5, resilience:1-5, documentation:1-5, creativity:1-5}}
- project_score: float 0-10
- project_feedback: string
- overall_summary: string (2-4 sentences)
"""


def process_job(job_id, model_slug):
    """
    Background worker: processes a Job by calling OpenRouter,
    validating the response, and saving it.
    """
    job = Job.objects.get(id=job_id)
    job.status = "processing"
    job.save()

    cv_text = read_uploaded_file_text(job.cv_file) if job.cv_file else ""
    report_text = read_uploaded_file_text(job.report_file) if job.report_file else ""

    # You can store the real job description in settings or database.
    job_desc = getattr(
        settings,
        "JOB_DESCRIPTION_TEXT",
        "Backend Product Engineer: Django, REST, RAG, LLM"
    )
    rubric = (
        "Correctness (1-5), Code Quality (1-5), Resilience (1-5), "
        "Documentation (1-5), Creativity (1-5)"
    )

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": build_prompt(job_desc, cv_text, report_text, rubric)},
    ]

    try:
        out = call_openrouter_chat(
            model=model_slug,
            messages=messages,
            temperature=0.0,
            max_tokens=1200,
            retries=3,
        )

        try:
            validate_evaluation_result(out)
            job.result = out
            job.status = "completed"
            job.save()
        except Exception as ve:
            job.result = {"error": f"Validation failed: {ve}", "raw": out}
            job.status = "completed"
            job.save()
    except Exception as e:
        job.result = {"error": str(e), "trace": traceback.format_exc()}
        job.status = "completed"
        job.save()


class UploadView(APIView):
    """
    POST /upload
    Uploads a CV and project report, creates a Job.
    """
    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()  # status defaults to "queued"
            return Response(
                {"id": job.id, "status": job.status},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EvaluateView(APIView):
    """
    POST /evaluate
    Starts evaluation of a job by ID.
    Returns immediately with job status "queued".
    """
    def post(self, request):
        job_id = request.data.get("id")
        if not job_id:
            return Response({"error": "Provide job id"}, status=400)
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

        model_slug = config("OPENROUTER_MODEL", default="replace-this-with-model-slug")

        # Run evaluation in background
        t = threading.Thread(target=process_job, args=(job.id, model_slug), daemon=True)
        t.start()

        return Response({"id": job.id, "status": "queued"})


class ResultView(APIView):
    """
    GET /result/{id}
    Returns the current status and result of the evaluation job.
    """
    def get(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

        serializer = JobResultSerializer(job)
        return Response(serializer.data)
