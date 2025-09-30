import threading
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from decouple import config

from evaluator.models import Job
from evaluator.serializer import UploadSerializer, JobResultSerializer
from evaluator.utils import read_uploaded_file_text
from evaluator.llm import OpenRouterClient
from evaluator.validate import validate_evaluation_result


# ----- Constants -----
SYSTEM_INSTRUCTION = (
    'You are an expert backend hiring evaluator. '
    'YOU MUST RETURN ONLY A VALID JSON OBJECT and nothing else.'
)

DEFAULT_RUBRIC = (
    'Correctness (1-5), Code Quality (1-5), Resilience (1-5), '
    'Documentation (1-5), Creativity (1-5)'
)


# ----- Helpers -----
def build_prompt(job_desc: str, cv_text: str, report_text: str, rubric: str) -> str:
    """
    Build the structured prompt for the LLM evaluation.
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


def process_job(job_id: int, model_slug: str) -> None:
    """
    Background worker: processes a Job by calling the LLM,
    validating the response, and saving the result.
    """
    job = Job.objects.get(id=job_id)
    job.status = 'processing'
    job.save(update_fields=['status'])

    cv_text = read_uploaded_file_text(job.cv_file) if job.cv_file else ''
    report_text = read_uploaded_file_text(job.report_file) if job.report_file else ''

    job_desc = getattr(
        settings,
        'JOB_DESCRIPTION_TEXT',
        'Backend Product Engineer: Django, REST, RAG, LLM',
    )

    messages = [
        {'role': 'system', 'content': SYSTEM_INSTRUCTION},
        {'role': 'user', 'content': build_prompt(job_desc, cv_text, report_text, DEFAULT_RUBRIC)},
    ]

    client = OpenRouterClient()
    try:
        out = client.chat(
            model=model_slug,
            messages=messages,
            temperature=0.0,
            max_tokens=1200,
            retries=3,
        )

        # Validate and save
        try:
            validate_evaluation_result(out)
            job.result = out
        except Exception as ve:
            job.result = {'error': f'Validation failed: {ve}', 'raw': out}

        job.status = 'completed'
        job.save(update_fields=['result', 'status'])

    except Exception as e:
        job.result = {
            'error': str(e),
            'trace': traceback.format_exc(limit=2),
        }
        job.status = 'completed'
        job.save(update_fields=['result', 'status'])


# ----- API Views -----
class UploadView(APIView):
    """
    Upload a CV and project report, creates a Job entry.
    """
    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save()  # status defaults to 'queued'
            return Response({'id': job.id, 'status': job.status}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EvaluateView(APIView):
    """
    POST /evaluate
    Start evaluation for a given job_id.
    Runs asynchronously and returns immediately.
    """
    def post(self, request):
        job_id = request.data.get('id')
        if not job_id:
            return Response({'error': 'Provide job id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        model_slug = config('OPENROUTER_MODEL', default='openrouter/auto')

        # Launch background thread
        threading.Thread(target=process_job, args=(job.id, model_slug), daemon=True).start()

        return Response({'id': job.id, 'status': 'queued'})


class ResultView(APIView):
    """
    GET /result/{id}
    Retrieve the current status and result of the evaluation job.
    """
    def get(self, request, job_id: int):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = JobResultSerializer(job)
        return Response(serializer.data)
