from django.db import models
from patients.models import Patient
from departments.models import Department
from doctors.models import Doctor

def generate_appointment_id():
    year = '2026'
    last = Appointment.objects.filter(appointment_id__startswith=f'APT-{year}-').order_by('-appointment_id').first()
    if last:
        num = int(last.appointment_id.split('-')[-1]) + 1
    else:
        num = 1
    return f'APT-{year}-{num:06d}'

class Appointment(models.Model):
    appointment_id = models.CharField(max_length=20, unique=True, default=generate_appointment_id)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'),('confirmed','Confirmed'),('completed','Completed'),('cancelled','Cancelled')], default='pending')
    payment_status = models.CharField(max_length=20, choices=[
        ('unpaid','Unpaid'),('paid','Paid'),('failed','Failed')], default='unpaid')
    esewa_ref = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.full_name}"
