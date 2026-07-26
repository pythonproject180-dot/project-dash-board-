from django.shortcuts import render
from departments.models import Department
from doctors.models import Doctor
from .models import Testimonial, GalleryImage, DiseaseInfo

def home(request):
    departments = Department.objects.filter(is_active=True)[:6]
    doctors = Doctor.objects.filter(is_active=True)[:8]
    testimonials = Testimonial.objects.filter(is_active=True)[:4]
    context = {
        'departments': departments, 'doctors': doctors, 'testimonials': testimonials,
        'total_departments': departments.count(), 'total_doctors': Doctor.objects.filter(is_active=True).count(),
    }
    return render(request, 'website/home.html', context)

def about(request):
    return render(request, 'website/about.html')

def departments_page(request):
    departments = Department.objects.filter(is_active=True)
    return render(request, 'website/departments.html', {'departments': departments})

def doctors_page(request):
    doctors = Doctor.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    return render(request, 'website/doctors.html', {'doctors': doctors, 'departments': departments})

def diseases(request):
    diseases = DiseaseInfo.objects.filter(is_active=True)
    return render(request, 'website/diseases.html', {'diseases': diseases})

def gallery(request):
    images = GalleryImage.objects.filter(is_active=True)
    return render(request, 'website/gallery.html', {'images': images})

def contact(request):
    return render(request, 'website/contact.html')

def services(request):
    departments = Department.objects.filter(is_active=True)
    return render(request, 'website/services.html', {'departments': departments})

def appointment(request):
    """Book appointment — integrated with doctor quota system."""
    if request.method == "POST":
        from appointments.models import Appointment
        from django.utils import timezone
        # Check doctor quota
        doctor_id = request.POST.get("doctor")
        appointment_date = request.POST.get("appointment_date")
        if doctor_id and appointment_date:
            from doctors.models import DoctorQuota
            date_obj = timezone.datetime.strptime(appointment_date, "%Y-%m-%d").date()
            quota = DoctorQuota.objects.filter(doctor_id=doctor_id, weekday=date_obj.weekday(), is_active=True).first()
            if quota:
                booked = Appointment.objects.filter(doctor_id=doctor_id, appointment_date=appointment_date).count()
                if booked >= quota.max_patients:
                    departments = Department.objects.filter(is_active=True)
                    doctors = Doctor.objects.filter(is_active=True)
                    return render(request, "website/appointment.html", {
                        "error": f"Dr. {quota.doctor.name} quota is full for this day. Please select another date.",
                        "departments": departments, "doctors": doctors,
                    })
        Appointment.objects.create(
            patient_id=request.POST.get("patient") if request.POST.get("patient") else None,
            department_id=request.POST.get("department"),
            doctor_id=request.POST.get("doctor"),
            appointment_date=request.POST.get("appointment_date"),
            appointment_time=request.POST.get("appointment_time") or None,
            notes=request.POST.get("notes", ""),
        )
        return render(request, "website/appointment_success.html")
    departments = Department.objects.filter(is_active=True)
    doctors = Doctor.objects.filter(is_active=True)
    return render(request, "website/appointment.html", {"departments": departments, "doctors": doctors})

def appointment_success(request):
    return render(request, "website/appointment_success.html")

