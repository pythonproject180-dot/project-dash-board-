# RadiologyRequest is in consultations/models.py
# This app provides radiology-specific views

from django.db import models

class RadiologyCatalog(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imaging_type = models.CharField(max_length=50, choices=[
        ('xray','X-Ray'),('ct','CT'),('mri','MRI'),('ecg','ECG'),('echo','Echo'),('ultrasound','Ultrasound')])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
