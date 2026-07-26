from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from .models import Ward, Bed, Admission, DischargeSummary
from patients.models import Patient
from doctors.models import Doctor
from accounts.decorators import admission_required, super_admin_required, doctor_required
from utils.pdf_utils import download_as_pdf, download_as_image
from accounts.models import AuditLog


def fmt(amount):
    try:
        amt = float(amount)
        if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
        else: return f'NPR {amt:,.0f}'
    except: return f'NPR {amount}'


@login_required
@admission_required
def admission_dashboard(request):
    """Admission Dashboard with bed availability stats, popup modals, charts."""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(is_occupied=True).count()
    available_beds = total_beds - occupied_beds
    admitted = Admission.objects.filter(status='admitted').count()
    admitted_today = Admission.objects.filter(admission_date__date=today).count()
    discharged_today = Admission.objects.filter(status='discharged', discharge_date__date=today).count() if hasattr(Admission, 'discharge_date') else 0
    total_admitted = Admission.objects.filter(status='admitted').count()
    total_discharged = Admission.objects.filter(status='discharged').count()

    wards = Ward.objects.filter(is_active=True).annotate(
        total_beds=Count('bed'),
        occupied_beds=Count('bed', filter=Q(bed__is_occupied=True)),
    )

    # Popup data
    pending = Admission.objects.filter(status='admitted').select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')[:30]
    today_admissions_list = Admission.objects.filter(admission_date__date=today).select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')[:30]
    recent_discharges_list = Admission.objects.filter(status='discharged').select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')[:20] if hasattr(Admission, 'discharge_date') else []

    # Chart data: admissions per day (last 7 days)
    import datetime
    chart_days = []
    chart_admissions = []
    chart_discharges = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_admissions.append(Admission.objects.filter(admission_date__date=d).count())
        chart_discharges.append(Admission.objects.filter(status='discharged', discharge_date__date=d).count() if hasattr(Admission, 'discharge_date') else 0)

    context = {
        'total_beds': total_beds, 'occupied_beds': occupied_beds,
        'available_beds': available_beds, 'admitted': admitted,
        'admitted_today': admitted_today, 'discharged_today': discharged_today,
        'total_admitted': total_admitted, 'total_discharged': total_discharged,
        'wards': wards, 'pending': pending,
        'today_admissions_list': today_admissions_list,
        'recent_discharges_list': recent_discharges_list,
        'chart_days': chart_days,
        'chart_admissions': chart_admissions,
        'chart_discharges': chart_discharges,
        'role': request.user.role,
    }
    return render(request, 'dashboard/admission.html', context)


@login_required
@admission_required
def admission_list(request):
    """Admission list with search/filter."""
    query = request.GET.get('q', '')
    admissions = Admission.objects.filter(status='admitted').order_by('-admission_date')
    if query:
        admissions = admissions.filter(
            Q(admission_id__icontains=query) |
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query)
        )
    return render(request, 'dashboard/admission_list.html', {
        'admissions': admissions, 'query': query, 'role': request.user.role,
    })


@login_required
@admission_required
def admit_patient(request):
    """Admit patient with bed assignment."""
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        doctor_id = request.POST.get('doctor')
        ward_id = request.POST.get('ward')
        bed_id = request.POST.get('bed')
        diagnosis = request.POST.get('diagnosis', '')

        patient = get_object_or_404(Patient, pk=patient_id)
        bed = get_object_or_404(Bed, pk=bed_id)

        admission = Admission.objects.create(
            patient=patient,
            doctor_id=doctor_id,
            ward_id=ward_id,
            bed=bed,
            diagnosis=diagnosis,
            created_by=request.user,
        )

        # Mark bed as occupied
        bed.is_occupied = True
        bed.save()

        # Auto-attach to medical record
        from medical_records.models import MedicalRecord
        MedicalRecord.objects.create(
            patient=patient, department='admission',
            record_type='admission_record',
            title=f'Admission - {admission.admission_id}',
            summary=f'Admitted to {bed}. Diagnosis: {diagnosis}',
            uploaded_by=str(request.user), staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action='Admit Patient', module='admissions',
            detail=f'{admission.admission_id}', patient_id=patient.patient_id,
        )
        return redirect(f'/patients/detail/{patient.pk}/')

    patients = Patient.objects.all().order_by('-created_at')
    doctors = Doctor.objects.filter(is_active=True)
    wards = Ward.objects.filter(is_active=True)
    beds = Bed.objects.filter(is_occupied=False)
    return render(request, 'dashboard/admit_patient.html', {
        'patients': patients, 'doctors': doctors, 'wards': wards, 'beds': beds,
        'role': request.user.role,
    })


@login_required
@admission_required
def discharge_patient(request, pk):
    """Discharge patient with formal Discharge Summary."""
    admission = get_object_or_404(Admission, pk=pk)
    if request.method == 'POST':
        # Create Discharge Summary
        discharge = DischargeSummary.objects.create(
            admission=admission,
            patient=admission.patient,
            attending_doctor=admission.doctor,
            admission_diagnosis=admission.diagnosis,
            final_diagnosis=request.POST.get('final_diagnosis', ''),
            chief_complaint=request.POST.get('chief_complaint', ''),
            history_of_present_illness=request.POST.get('history_illness', ''),
            examination_findings=request.POST.get('examination_findings', ''),
            investigations=request.POST.get('investigations', ''),
            treatment_given=request.POST.get('treatment_given', ''),
            condition_at_discharge=request.POST.get('condition', 'improved'),
            discharge_instructions=request.POST.get('discharge_instructions', ''),
            follow_up_date=request.POST.get('follow_up_date') or None,
            follow_up_instructions=request.POST.get('follow_up_instructions', ''),
            medications_at_discharge=request.POST.get('medications', ''),
            prepared_by=request.user,
        )

        # Discharge admission
        admission.discharge()

        # Auto-attach to medical record
        from medical_records.models import MedicalRecord
        MedicalRecord.objects.create(
            patient=admission.patient, department='admission',
            record_type='uploaded_pdf',
            title=f'Discharge Summary - {admission.admission_id}',
            summary=f'Condition: {discharge.condition_at_discharge}. Instructions: {discharge.discharge_instructions}',
            uploaded_by=str(request.user), staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action='Discharge Patient', module='admissions',
            detail=f'{admission.admission_id}', patient_id=admission.patient.patient_id,
        )

        return render(request, 'dashboard/discharge_summary_print.html', {
            'discharge': discharge, 'admission': admission,
            'role': request.user.role,
        })

    context = {
        'admission': admission,
        'role': request.user.role,
    }
    return render(request, 'dashboard/discharge.html', context)


@login_required
def admission_search(request):
    """Search admissions by Hospital ID, Name, Phone."""
    query = request.GET.get('q', '')
    admissions = Admission.objects.all().order_by('-admission_date')
    if query:
        admissions = admissions.filter(
            Q(admission_id__icontains=query) |
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(patient__phone__icontains=query)
        )
    return render(request, 'dashboard/admission_search.html', {
        'admissions': admissions, 'query': query, 'role': request.user.role,
    })


@login_required
def discharge_summary_pdf(request, pk):
    """Download Discharge Summary as PDF."""
    discharge = get_object_or_404(DischargeSummary, pk=pk)
    context = {'discharge': discharge, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/discharge_summary_print.html', context,
                           filename=f'DischargeSummary-{discharge.patient.patient_id}.pdf', request=request)


@login_required
def discharge_summary_jpg(request, pk):
    """Download Discharge Summary as JPG."""
    discharge = get_object_or_404(DischargeSummary, pk=pk)
    context = {'discharge': discharge, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/discharge_summary_print.html', context,
                             filename=f'DischargeSummary-{discharge.patient.patient_id}.jpg', request=request)
