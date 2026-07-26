from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum
from .models import Doctor, DoctorQuota, WEEKDAY_CHOICES
from patients.models import OPDVisit, Patient
from departments.models import Department
from accounts.models import AuditLog
from accounts.decorators import doctor_required, super_admin_required
from utils.pdf_utils import download_as_pdf, download_as_image


def fmt(amount):
    try:
        amt = float(amount)
        if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
        else: return f'NPR {amt:,.0f}'
    except: return f'NPR {amount}'


@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor Dashboard — shows patients today/month/year stats, waiting queue, quota management."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    doctor = Doctor.objects.filter(user_account=request.user).first()

    # Stats
    patients_today = OPDVisit.objects.filter(doctor=doctor, visit_date__date=today).count() if doctor else 0
    patients_month = OPDVisit.objects.filter(doctor=doctor, visit_date__date__gte=month_start).count() if doctor else 0
    patients_year = OPDVisit.objects.filter(doctor=doctor, visit_date__date__gte=year_start).count() if doctor else 0

    queue = OPDVisit.objects.filter(doctor=doctor, status='waiting').order_by('token_number') if doctor else []
    completed = OPDVisit.objects.filter(doctor=doctor, status='completed').order_by('-visit_date')[:20] if doctor else []

    # Quota info
    quotas = DoctorQuota.objects.filter(doctor=doctor) if doctor else []
    today_quota = DoctorQuota.objects.filter(doctor=doctor, weekday=today.weekday(), is_active=True).first() if doctor else None

    context = {
        'doctor': doctor,
        'queue': queue,
        'completed': completed,
        'patients_today': patients_today,
        'patients_month': patients_month,
        'patients_year': patients_year,
        'quotas': quotas,
        'today_quota': today_quota,
        'role': 'doctor',
    }
    return render(request, 'dashboard/doctor.html', context)


@login_required
@doctor_required
def doctor_manage_quota(request):
    """Doctor OPD Quota Management — create/edit daily quotas."""
    doctor = Doctor.objects.filter(user_account=request.user).first()
    if not doctor:
        return redirect(request.user.get_dashboard_url())

    if request.method == 'POST':
        # Update or create quotas for each weekday
        for weekday_num, weekday_name in WEEKDAY_CHOICES:
            max_patients = request.POST.get(f'max_{weekday_num}', 50)
            start_time = request.POST.get(f'start_{weekday_num}', '09:00')
            end_time = request.POST.get(f'end_{weekday_num}', '14:00')
            is_active = request.POST.get(f'active_{weekday_num}') == 'on'

            quota = DoctorQuota.objects.filter(doctor=doctor, weekday=weekday_num).first()
            if quota:
                quota.max_patients = max_patients
                quota.start_time = start_time
                quota.end_time = end_time
                quota.is_active = is_active
                quota.save()
            else:
                DoctorQuota.objects.create(
                    doctor=doctor, weekday=weekday_num,
                    max_patients=max_patients, start_time=start_time,
                    end_time=end_time, is_active=is_active,
                )

        AuditLog.objects.create(
            user=request.user, action='Manage OPD Quota', module='doctors',
            detail=f'Dr. {doctor.name}',
        )
        return redirect('/doctors/dashboard/')

    quotas = DoctorQuota.objects.filter(doctor=doctor)
    context = {
        'doctor': doctor, 'quotas': quotas,
        'weekday_choices': WEEKDAY_CHOICES,
        'role': 'doctor',
    }
    return render(request, 'dashboard/doctor_quota.html', context)


@login_required
@doctor_required
def consultation_create(request, visit_pk):
    """Doctor consultation — write notes, prescription, request lab/radiology."""
    from patients.models import OPDVisit
    from consultations.models import Consultation, Prescription, LabTestRequest, RadiologyRequest
    from laboratory.models import LabCatalog
    from radiology.models import RadiologyCatalog

    visit = get_object_or_404(OPDVisit, pk=visit_pk)
    patient = visit.patient

    if request.method == 'POST':
        # Create consultation
        consultation = Consultation.objects.create(
            visit=visit,
            doctor=visit.doctor,
            diagnosis=request.POST.get('diagnosis', ''),
            clinical_notes=request.POST.get('clinical_notes', ''),
            follow_up_date=request.POST.get('follow_up_date') or None,
        )

        # Add prescriptions (dynamic add/remove)
        med_names = request.POST.getlist('med_name[]')
        dosages = request.POST.getlist('dosage[]')
        frequencies = request.POST.getlist('frequency[]')
        durations = request.POST.getlist('duration[]')
        instructions = request.POST.getlist('instructions[]')

        for i in range(len(med_names)):
            if med_names[i]:
                pres = Prescription.objects.create(
                    medicine_name=med_names[i],
                    dosage=dosages[i] if i < len(dosages) else '',
                    frequency=frequencies[i] if i < len(frequencies) else '',
                    duration=durations[i] if i < len(durations) else '',
                    instructions=instructions[i] if i < len(instructions) else '',
                )
                consultation.prescriptions.add(pres)

        # Request lab tests
        lab_test_ids = request.POST.getlist('lab_tests')
        for catalog_id in lab_test_ids:
            catalog = LabCatalog.objects.get(pk=catalog_id)
            LabTestRequest.objects.create(
                patient=patient,
                consultation=consultation,
                doctor=visit.doctor,
                test_name=catalog.name,
            )

        # Request radiology
        rad_test_ids = request.POST.getlist('radiology_tests')
        for catalog_id in rad_test_ids:
            catalog = RadiologyCatalog.objects.get(pk=catalog_id)
            RadiologyRequest.objects.create(
                patient=patient,
                consultation=consultation,
                doctor=visit.doctor,
                imaging_type=catalog.imaging_type,
                custom_type=catalog.name,
            )

        # Mark visit as completed
        visit.status = 'completed'
        visit.save()

        # Auto-attach to medical record
        from medical_records.models import MedicalRecord
        MedicalRecord.objects.create(
            patient=patient, department='doctors',
            record_type='doctor_note',
            title=f'Consultation - {patient.patient_id}',
            summary=f'Diagnosis: {consultation.diagnosis}',
            uploaded_by=str(request.user), staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action='Consultation', module='consultations',
            detail=f'{patient.patient_id}', patient_id=patient.patient_id,
        )

        return redirect(f'/patients/detail/{patient.pk}/')

    lab_catalogs = LabCatalog.objects.filter(is_active=True)
    radiology_catalogs = RadiologyCatalog.objects.filter(is_active=True)

    context = {
        'visit': visit, 'patient': patient,
        'lab_catalogs': lab_catalogs,
        'radiology_catalogs': radiology_catalogs,
        'role': 'doctor',
    }
    return render(request, 'dashboard/consultation_form.html', context)


@login_required
@super_admin_required
def doctor_list(request):
    """Doctor list — Super Admin only."""
    doctors = Doctor.objects.all()
    return render(request, 'dashboard/doctor_list.html', {'doctors': doctors, 'role': 'super_admin'})


@login_required
@super_admin_required
def doctor_add(request):
    """Add doctor — Super Admin only."""
    if request.method == 'POST':
        doc = Doctor.objects.create(
            name=request.POST.get('name'),
            department_id=request.POST.get('department'),
            qualification=request.POST.get('qualification'),
            specialization=request.POST.get('specialization'),
            consultation_fee=request.POST.get('consultation_fee', 0),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            schedule=request.POST.get('schedule'),
            photo=request.FILES.get('photo'),
        )
        AuditLog.objects.create(user=request.user, action='Create Doctor', module='doctors', detail=doc.name)
        return redirect('/doctors/list/')
    return render(request, 'dashboard/doctor_form.html', {
        'departments': Department.objects.all(), 'role': 'super_admin', 'action': 'Add',
    })


@login_required
@super_admin_required
def doctor_edit(request, pk):
    """Edit doctor — Super Admin only."""
    doc = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        doc.name = request.POST.get('name')
        doc.department_id = request.POST.get('department')
        doc.qualification = request.POST.get('qualification')
        doc.specialization = request.POST.get('specialization')
        doc.consultation_fee = request.POST.get('consultation_fee', 0)
        doc.phone = request.POST.get('phone')
        doc.email = request.POST.get('email')
        doc.schedule = request.POST.get('schedule')
        if request.FILES.get('photo'):
            doc.photo = request.FILES.get('photo')
        doc.save()
        AuditLog.objects.create(user=request.user, action='Edit Doctor', module='doctors', detail=doc.name)
        return redirect('/doctors/list/')
    return render(request, 'dashboard/doctor_form.html', {
        'doctor': doc, 'departments': Department.objects.all(),
        'role': 'super_admin', 'action': 'Edit',
    })


@login_required
@super_admin_required
def doctor_delete(request, pk):
    """Delete doctor — Super Admin only."""
    doc = get_object_or_404(Doctor, pk=pk)
    AuditLog.objects.create(user=request.user, action='Delete Doctor', module='doctors', detail=doc.name)
    doc.delete()
    return redirect('/doctors/list/')
