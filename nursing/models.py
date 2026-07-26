from django.db import models
from patients.models import Patient

class NursingNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    note_type = models.CharField(max_length=50, choices=[
        ('nursing_note','Nursing Note'),('vital_signs','Vital Signs'),('progress','Progress Note'),
        ('observation','Observation'),('medication_admin','Medication Administration')], default='nursing_note')
    content = models.TextField()
    vital_bp = models.CharField(max_length=50, blank=True)
    vital_temp = models.CharField(max_length=50, blank=True)
    vital_pulse = models.CharField(max_length=50, blank=True)
    vital_resp = models.CharField(max_length=50, blank=True)
    attached_file = models.FileField(upload_to='nursing_docs/', blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.note_type} - {self.patient.full_name}"
