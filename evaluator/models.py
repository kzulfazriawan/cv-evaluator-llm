from django.db import models

# Create your models here.
class Job(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('finished', 'Finished'),
    )

    cv_file = models.FileField(upload_to='uploads/cv/', null=True, blank=True)
    report_file = models.FileField(upload_to='uploads/report/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Job {self.pk} - {self.status}'

