from django.db import models
from patients.models import Patient

class PortalUser(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Portal: {self.patient.full_name}"
