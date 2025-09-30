from rest_framework import serializers
from .models import Job


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "cv_file", "report_file"]


class JobResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ["id", "status", "result", "created_at"]
