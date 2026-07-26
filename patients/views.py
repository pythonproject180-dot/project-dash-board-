from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.conf import settings
from .models import Patient, OPDVisit
from departments.models import Department
from doctors.models import Doctor, DoctorQuota
from accounts.models import AuditLog, Province, District
from accounts.decorators import registration_required, super_admin_required, doctor_required
from utils.pdf_utils import download_as_pdf, download_as_image


def format_nepal_amount(amount):
    """Format large amounts in Lakh/Crore notation."""
    try:
        amt = float(amount)
        if amt >= 10000000:
            return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000:
            return f'{amt/100000:.2f} Lakh'
        else:
            return f'NPR {amt:,.0f}'
    except (ValueError, TypeError):
        return f'NPR {amount}'


@login_required
@registration_required
def registration_dashboard(request):
    """Registration Counter Dashboard — shows today/monthly/yearly stats with popup cards."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    # Registration stats
    today_registrations = Patient.objects.filter(created_at__date=today).count()
    month_registrations = Patient.objects.filter(created_at__date__gte=month_start).count()
    year_registrations = Patient.objects.filter(created_at__date__gte=year_start).count()
    total_patients = Patient.objects.count()

    # Collection stats
    today_collection_raw = OPDVisit.objects.filter(visit_date__date=today).aggregate(total=Sum('registration_fee'))['total'] or 0
    month_collection_raw = OPDVisit.objects.filter(visit_date__date__gte=month_start).aggregate(total=Sum('registration_fee'))['total'] or 0
    year_collection_raw = OPDVisit.objects.filter(visit_date__date__gte=year_start).aggregate(total=Sum('registration_fee'))['total'] or 0

    # Detailed fees breakdown for popup
    today_new_fees = OPDVisit.objects.filter(visit_date__date=today, visit_type='new').aggregate(total=Sum('registration_fee'))['total'] or 0
    today_followup_fees = OPDVisit.objects.filter(visit_date__date=today, visit_type='follow_up').aggregate(total=Sum('registration_fee'))['total'] or 0

    # Queue stats
    waiting = OPDVisit.objects.filter(status='waiting').count()
    in_progress = OPDVisit.objects.filter(status='in_progress').count()
    completed_today = OPDVisit.objects.filter(status='completed', visit_date__date=today).count()

    # Available doctor quotas
    doctor_quotas = DoctorQuota.objects.filter(
        weekday=today.weekday(), is_active=True
    ).select_related('doctor')

    departments = Department.objects.filter(is_active=True)

    # Popup modal data
    today_patient_list = Patient.objects.filter(created_at__date=today).order_by('-created_at')[:30]
    month_patient_list = Patient.objects.filter(created_at__date__gte=month_start).order_by('-created_at')[:30]
    queue_list = OPDVisit.objects.filter(status__in=('waiting', 'in_progress')).select_related('patient', 'doctor', 'department').order_by('token_number')[:30]

    # Chart data: registrations per day (last 7 days)
    import datetime as dt
    chart_days = []
    chart_registrations = []
    chart_collections = []
    for i in range(6, -1, -1):
        d = today - dt.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_registrations.append(Patient.objects.filter(created_at__date=d).count())
        chart_collections.append(float(OPDVisit.objects.filter(visit_date__date=d).aggregate(total=Sum('registration_fee'))['total'] or 0))

    context = {
        'today_registrations': today_registrations,
        'month_registrations': month_registrations,
        'year_registrations': year_registrations,
        'total_patients': total_patients,
        'today_collection': format_nepal_amount(today_collection_raw),
        'today_collection_raw': today_collection_raw,
        'month_collection': format_nepal_amount(month_collection_raw),
        'month_collection_raw': month_collection_raw,
        'year_collection': format_nepal_amount(year_collection_raw),
        'year_collection_raw': year_collection_raw,
        'today_new_fees': today_new_fees,
        'today_followup_fees': today_followup_fees,
        'waiting': waiting,
        'in_progress': in_progress,
        'completed_today': completed_today,
        'doctor_quotas': doctor_quotas,
        'departments': departments,
        'today_patient_list': today_patient_list,
        'month_patient_list': month_patient_list,
        'queue_list': queue_list,
        'today': today,
        'month_start': month_start,
        'chart_days': chart_days,
        'chart_registrations': chart_registrations,
        'chart_collections': chart_collections,
        'role': request.user.role,
    }
    return render(request, 'dashboard/registration.html', context)


@login_required
def patient_list(request):
    """Patient list with search/filter support."""
    query = request.GET.get('q', '')
    patients = Patient.objects.all().order_by('-created_at')
    if query:
        patients = patients.filter(
            Q(patient_id__icontains=query) |
            Q(full_name__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query)
        )
    context = {'patients': patients, 'query': query, 'role': request.user.role}
    return render(request, 'dashboard/patient_list.html', context)


@login_required
@registration_required
def patient_register(request):
    """Register a new patient with OPD visit — checks doctor quota."""
    if request.method == 'POST':
        province_id = request.POST.get('province')
        district_id = request.POST.get('district')
        dept_id = request.POST.get('department')
        doctor_id = request.POST.get('doctor')

        # Check doctor quota
        if doctor_id:
            today = timezone.now().date()
            quota = DoctorQuota.objects.filter(
                doctor_id=doctor_id, weekday=today.weekday(), is_active=True
            ).first()
            if quota and quota.is_quota_full:
                doctors = Doctor.objects.filter(is_active=True)
                departments = Department.objects.filter(is_active=True)
                provinces = Province.objects.all()
                districts = District.objects.all()
                context = {
                    'error': f'Dr. {quota.doctor.name} quota is full for today ({quota.max_patients} patients). Please select another doctor.',
                    'doctors': doctors, 'departments': departments,
                    'provinces': provinces, 'districts': districts,
                    'role': request.user.role,
                }
                return render(request, 'dashboard/patient_register.html', context)

        # Determine if new or returning patient
        phone = request.POST.get('phone')
        existing_patient = Patient.objects.filter(phone=phone).first()

        if existing_patient:
            # Returning patient — create new OPD visit
            existing_patient.first_name = request.POST.get('first_name', existing_patient.first_name)
            existing_patient.last_name = request.POST.get('last_name', existing_patient.last_name)
            existing_patient.is_new_patient = False
            existing_patient.save()
            patient = existing_patient
            fee = settings.REGISTRATION_FEE_OLD  # 50 NPR
        else:
            # New patient
            patient = Patient.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                age_value=request.POST.get('age_value', 0),
                age_type=request.POST.get('age_type', 'years'),
                gender=request.POST.get('gender'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email', ''),
                address_line=request.POST.get('address_line', ''),
                province_id=province_id,
                district_id=district_id,
                municipality=request.POST.get('municipality', ''),
                ward_number=request.POST.get('ward', ''),
                tole=request.POST.get('tole', ''),
                emergency_contact_name=request.POST.get('emergency_contact_name', ''),
                emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),
                emergency_contact_relation=request.POST.get('emergency_contact_relation', ''),
                blood_group=request.POST.get('blood_group', ''),
                allergies=request.POST.get('allergies', ''),
                chronic_conditions=request.POST.get('chronic_conditions', ''),
                photo=request.FILES.get('photo'),
                registered_by=request.user,
                registration_source='counter',
                is_new_patient=True,
            )
            fee = settings.REGISTRATION_FEE_NEW  # 100 NPR

        # Create OPD Visit
        today = timezone.now().date()
        last_token = OPDVisit.objects.filter(visit_date__date=today).order_by('-token_number').first()
        token = (last_token.token_number + 1) if last_token else 1

        visit_type = 'new' if patient.is_new_patient else 'follow_up'
        payment_method = request.POST.get('payment_method', 'cash')

        visit = OPDVisit.objects.create(
            patient=patient,
            doctor_id=doctor_id,
            department_id=dept_id,
            token_number=token,
            registration_fee=fee,
            payment_method=payment_method,
            visit_type=visit_type,
            created_by=request.user,
        )

        # Auto-attach to medical record
        from medical_records.models import MedicalRecord
        MedicalRecord.objects.create(
            patient=patient,
            department='registration',
            record_type='uploaded_pdf',
            title=f'OPD Registration - {patient.patient_id}',
            summary=f'Patient registered for OPD visit. Token #{token}. Fee: NPR {fee}',
            uploaded_by=str(request.user),
            staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action='Register Patient', module='patients',
            detail=f'{patient.patient_id} - Token #{token}', patient_id=patient.patient_id
        )

        return render(request, 'dashboard/opd_ticket.html', {
            'patient': patient, 'visit': visit, 'role': request.user.role,
        })

    provinces = Province.objects.all()
    districts = District.objects.all()
    departments = Department.objects.filter(is_active=True)
    doctors = Doctor.objects.filter(is_active=True)
    # Doctor quotas for today
    today = timezone.now().date()
    doctor_quotas = DoctorQuota.objects.filter(weekday=today.weekday(), is_active=True)

    return render(request, 'dashboard/patient_register.html', {
        'provinces': provinces, 'districts': districts,
        'departments': departments, 'doctors': doctors,
        'doctor_quotas': doctor_quotas,
        'role': request.user.role,
    })


@login_required
def patient_detail(request, pk):
    """Patient detail — comprehensive profile with all related records."""
    patient = get_object_or_404(Patient, pk=pk)
    visits = OPDVisit.objects.filter(patient=patient)
    from billing.models import Bill, BillItem
    from admissions.models import Admission, DischargeSummary
    from consultations.models import LabTestRequest, RadiologyRequest
    from pharmacy.models import PharmacySale
    from insurance.models import InsuranceClaim
    from medical_records.models import MedicalRecord

    bills = Bill.objects.filter(patient=patient).order_by('-created_at')[:10]
    admissions = Admission.objects.filter(patient=patient).order_by('-admission_date')[:10]
    lab_results = LabTestRequest.objects.filter(patient=patient).order_by('-created_at')[:10]
    radiology = RadiologyRequest.objects.filter(patient=patient).order_by('-created_at')[:10]
    pharmacy = PharmacySale.objects.filter(patient=patient).order_by('-sale_date')[:10]
    insurance_claims = InsuranceClaim.objects.filter(patient=patient).order_by('-created_at')[:10]
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')[:20]

    # Check if can print patient card (only registration and super_admin)
    can_print_card = request.user.role in ('registration', 'super_admin') or request.user.is_superuser

    context = {
        'patient': patient, 'visits': visits, 'bills': bills,
        'admissions': admissions, 'lab_results': lab_results,
        'radiology': radiology, 'pharmacy': pharmacy,
        'insurance_claims': insurance_claims,
        'medical_records': medical_records,
        'can_print_card': can_print_card,
        'role': request.user.role,
    }
    return render(request, 'dashboard/patient_detail.html', context)


@login_required
def patient_search(request):
    """Search patients by Hospital ID, Name, Phone, QR, Insurance Number."""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    results = []
    if query:
        if search_type == 'id':
            results = Patient.objects.filter(patient_id__icontains=query)
        elif search_type == 'phone':
            results = Patient.objects.filter(phone__icontains=query)
        elif search_type == 'name':
            results = Patient.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(full_name__icontains=query)
            )
        elif search_type == 'insurance':
            from insurance.models import PatientInsurance
            ins = PatientInsurance.objects.filter(policy_number__icontains=query)
            results = [i.patient for i in ins]
        else:
            results = Patient.objects.filter(
                Q(patient_id__icontains=query) |
                Q(full_name__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone__icontains=query)
            )
    return render(request, 'dashboard/patient_search.html', {
        'results': results, 'query': query, 'search_type': search_type,
        'role': request.user.role,
    })


@login_required
def patient_card(request, pk):
    """Patient Card — only registration and super_admin can access."""
    if request.user.role not in ('registration', 'super_admin') and not request.user.is_superuser:
        return redirect(request.user.get_dashboard_url())
    patient = get_object_or_404(Patient, pk=pk)
    size = request.GET.get('size', 'id')
    context = {'patient': patient, 'role': request.user.role, 'size': size}
    return render(request, 'dashboard/patient_card.html', context)


@login_required
def patient_card_pdf(request, pk):
    """Download Patient Card as PDF — only registration and super_admin."""
    if request.user.role not in ('registration', 'super_admin') and not request.user.is_superuser:
        return redirect(request.user.get_dashboard_url())
    patient = get_object_or_404(Patient, pk=pk)
    size = request.GET.get('size', 'id')
    context = {'patient': patient, 'role': request.user.role, 'size': size, 'is_pdf': True}
    return download_as_pdf('dashboard/patient_card.html', context, filename=f'PatientCard-{patient.patient_id}.pdf', request=request)


@login_required
def patient_card_jpg(request, pk):
    """Download Patient Card as JPG image — only registration and super_admin."""
    if request.user.role not in ('registration', 'super_admin') and not request.user.is_superuser:
        return redirect(request.user.get_dashboard_url())
    patient = get_object_or_404(Patient, pk=pk)
    size = request.GET.get('size', 'id')
    context = {'patient': patient, 'role': request.user.role, 'size': size, 'is_pdf': True}
    return download_as_image('dashboard/patient_card.html', context, filename=f'PatientCard-{patient.patient_id}.jpg', request=request)


@login_required
def opd_ticket_pdf(request, pk):
    """Download OPD Ticket as PDF."""
    visit = get_object_or_404(OPDVisit, pk=pk)
    patient = visit.patient
    context = {'patient': patient, 'visit': visit, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/opd_ticket.html', context, filename=f'OPD-Ticket-{patient.patient_id}.pdf', request=request)


@login_required
def opd_ticket_jpg(request, pk):
    """Download OPD Ticket as JPG image."""
    visit = get_object_or_404(OPDVisit, pk=pk)
    patient = visit.patient
    context = {'patient': patient, 'visit': visit, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/opd_ticket.html', context, filename=f'OPD-Ticket-{patient.patient_id}.jpg', request=request)


@login_required
def bill_receipt_pdf(request, pk):
    """Download Bill Receipt as PDF."""
    from billing.models import Bill
    bill = get_object_or_404(Bill, pk=pk)
    context = {'bill': bill, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/bill_receipt.html', context, filename=f'Bill-{bill.bill_id}.pdf', request=request)


@login_required
def bill_receipt_jpg(request, pk):
    """Download Bill Receipt as JPG image."""
    from billing.models import Bill
    bill = get_object_or_404(Bill, pk=pk)
    context = {'bill': bill, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/bill_receipt.html', context, filename=f'Bill-{bill.bill_id}.jpg', request=request)


@login_required
@registration_required
def patient_edit(request, pk):
    """Edit patient — Registration can edit within 24 hours only.
    After 24 hours, editing becomes disabled. Only Super Admin can modify after 24h.
    This is a critical business rule from the PDF specification.
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    # 24-hour edit restriction check
    time_since_creation = timezone.now() - patient.created_at
    hours_since_creation = time_since_creation.total_seconds() / 3600
    can_edit = False
    
    if request.user.role == 'super_admin' or request.user.is_superuser:
        can_edit = True  # Super Admin can edit anytime
    elif request.user.role == 'registration' and hours_since_creation <= 24:
        can_edit = True  # Registration can edit within 24 hours
    
    if not can_edit:
        context = {
            'patient': patient,
            'error': f'This patient was registered {hours_since_creation:.1f} hours ago. '
                     f'Only Super Admin can edit records after 24 hours.',
            'hours_since_creation': hours_since_creation,
            'role': request.user.role,
        }
        return render(request, 'dashboard/patient_edit.html', context)
    
    if request.method == 'POST':
        patient.first_name = request.POST.get('first_name', patient.first_name)
        patient.last_name = request.POST.get('last_name', patient.last_name)
        patient.age_value = request.POST.get('age_value', patient.age_value)
        patient.age_type = request.POST.get('age_type', patient.age_type)
        patient.gender = request.POST.get('gender', patient.gender)
        patient.phone = request.POST.get('phone', patient.phone)
        patient.email = request.POST.get('email', patient.email)
        patient.address_line = request.POST.get('address_line', patient.address_line)
        patient.municipality = request.POST.get('municipality', patient.municipality)
        patient.ward_number = request.POST.get('ward', patient.ward_number)
        patient.tole = request.POST.get('tole', patient.tole)
        patient.blood_group = request.POST.get('blood_group', patient.blood_group)
        patient.allergies = request.POST.get('allergies', patient.allergies)
        patient.chronic_conditions = request.POST.get('chronic_conditions', patient.chronic_conditions)
        patient.emergency_contact_name = request.POST.get('emergency_contact_name', patient.emergency_contact_name)
        patient.emergency_contact_phone = request.POST.get('emergency_contact_phone', patient.emergency_contact_phone)
        patient.emergency_contact_relation = request.POST.get('emergency_contact_relation', patient.emergency_contact_relation)
        if request.POST.get('province'):
            patient.province_id = request.POST.get('province')
        if request.POST.get('district'):
            patient.district_id = request.POST.get('district')
        if request.FILES.get('photo'):
            patient.photo = request.FILES.get('photo')
        patient.save()
        
        AuditLog.objects.create(
            user=request.user, action='Edit Patient', module='patients',
            detail=f'{patient.patient_id} - edited after {hours_since_creation:.1f} hours',
            patient_id=patient.patient_id,
        )
        return redirect(f'/patients/detail/{patient.pk}/')
    
    provinces = Province.objects.all()
    districts = District.objects.all()
    context = {
        'patient': patient, 'can_edit': can_edit,
        'hours_since_creation': hours_since_creation,
        'provinces': provinces, 'districts': districts,
        'role': request.user.role,
    }
    return render(request, 'dashboard/patient_edit.html', context)


@login_required
@registration_required
def patient_delete(request, pk):
    """Delete patient registration — only within 24 hours.
    After 24 hours, only Super Admin can delete.
    """
    patient = get_object_or_404(Patient, pk=pk)
    
    time_since_creation = timezone.now() - patient.created_at
    hours_since_creation = time_since_creation.total_seconds() / 3600
    can_delete = False
    
    if request.user.role == 'super_admin' or request.user.is_superuser:
        can_delete = True
    elif request.user.role == 'registration' and hours_since_creation <= 24:
        can_delete = True
    
    if not can_delete:
        return render(request, 'dashboard/patient_edit.html', {
            'patient': patient,
            'error': f'Cannot delete — registered {hours_since_creation:.1f} hours ago. Only Super Admin can delete after 24 hours.',
            'role': request.user.role,
        })
    
    if request.method == 'POST':
        patient_id = patient.patient_id
        patient.delete()
        AuditLog.objects.create(
            user=request.user, action='Delete Patient', module='patients',
            detail=f'Deleted {patient_id}',
        )
        return redirect('/patients/list/')
    
    context = {
        'patient': patient, 'can_delete': can_delete,
        'hours_since_creation': hours_since_creation,
        'role': request.user.role,
    }
    return render(request, 'dashboard/patient_delete_confirm.html', context)


@login_required
def patients_csv_export(request):
    """CSV export for patient registration data."""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Hospital ID', 'First Name', 'Last Name', 'Gender', 'Age', 'Phone', 'Email',
                     'Blood Group', 'Address', 'Registration Source', 'Is New Patient', 'Created At'])
    for patient in Patient.objects.all().order_by('-created_at'):
        writer.writerow([patient.patient_id, patient.first_name, patient.last_name,
                         patient.gender, patient.age_display, patient.phone, patient.email,
                         patient.blood_group, patient.address_display,
                         patient.registration_source, patient.is_new_patient,
                         patient.created_at.strftime('%Y-%m-%d')])
    return response
