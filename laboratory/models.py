# LabTestRequest is in consultations/models.py for cross-module integration
# This app provides the laboratory-specific views and dashboard

from django.db import models

class LabCatalog(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
