from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Appointment
from patients.models import Patient
from departments.models import Department
from doctors.models import Doctor

def appointment_book(request):
    departments = Department.objects.filter(is_active=True)
    doctors = Doctor.objects.filter(is_active=True)
    if request.method == 'POST':
        patient = Patient.objects.filter(patient_id=request.POST.get('patient_id')).first()
        if not patient:
            return render(request, 'website/appointment.html', {'departments': departments, 'doctors': doctors, 'error': 'Patient not found'})
        apt = Appointment.objects.create(
            patient=patient,
            department_id=request.POST.get('department'),
            doctor_id=request.POST.get('doctor'),
            appointment_date=request.POST.get('appointment_date'),
            appointment_time=request.POST.get('appointment_time'),
            notes=request.POST.get('notes', ''),
        )
        return render(request, 'website/appointment_success.html', {'appointment': apt})
    return render(request, 'website/appointment.html', {'departments': departments, 'doctors': doctors})
