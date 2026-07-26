from django.db import models
from patients.models import Patient
from doctors.models import Doctor

class Surgery(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    surgery_type = models.CharField(max_length=200)
    priority = models.CharField(max_length=20, choices=[
        ('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')], default='routine')
    clinical_notes = models.TextField(blank=True)
    consent_form = models.FileField(upload_to='ot_consent/', blank=True)
    planned_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled','Scheduled'),('in_progress','In Progress'),('completed','Completed'),('cancelled','Cancelled')], default='scheduled')
    operative_report = models.TextField(blank=True)
    surgical_notes = models.TextField(blank=True)
    procedure_summary = models.TextField(blank=True)
    result_file = models.FileField(upload_to='ot_results/', blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Surgery'
        verbose_name_plural = 'Surgery Schedule'

    def __str__(self):
        return f"{self.surgery_type} - {self.patient.full_name}"
