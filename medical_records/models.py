from django.db import models
from patients.models import Patient

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    department = models.CharField(max_length=100)
    record_type = models.CharField(max_length=50, choices=[
        ('doctor_note','Doctor Note'),('nursing_note','Nursing Note'),('lab_report','Lab Report'),
        ('radiology_report','Radiology Report'),('pharmacy_record','Pharmacy Record'),
        ('blood_bank_record','Blood Bank Record'),('admission_record','Admission Record'),
        ('ot_record','Operation Theatre Record'),('insurance_doc','Insurance Document'),
        ('uploaded_pdf','Uploaded PDF'),('uploaded_scan','Uploaded Scan'),('note','Note')], default='note')
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    file = models.FileField(upload_to='medical_records/', blank=True)
    uploaded_by = models.CharField(max_length=200, blank=True)
    staff_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.record_type} - {self.patient.full_name}"
