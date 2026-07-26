from django.db import models
from patients.models import Patient
from doctors.models import Doctor

BLOOD_GROUPS = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]

class BloodRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUPS)
    units_required = models.IntegerField(default=1)
    urgency = models.CharField(max_length=20, choices=[
        ('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')], default='routine')
    clinical_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'),('issued','Issued'),('completed','Completed')], default='pending')
    issued_units = models.IntegerField(default=0)
    issue_report = models.FileField(upload_to='blood_bank/', blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blood {self.blood_group} - {self.patient.full_name}"
