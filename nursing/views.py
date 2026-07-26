from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import NursingNote
from patients.models import Patient
from consultations.models import LabTestRequest, RadiologyRequest
from medical_records.models import MedicalRecord
from accounts.decorators import nursing_required
from accounts.models import AuditLog


@login_required
@nursing_required
def nursing_dashboard(request):
    """Nursing Dashboard — admitted patients, vitals, notes, with popup modals and chart data."""
    from django.utils import timezone
    from admissions.models import Admission
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Currently admitted patients (assigned to nursing)
    assigned = Admission.objects.filter(status='admitted').select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')[:30]

    # Stats
    today_admissions = Admission.objects.filter(admission_date__date=today).count()
    today_discharges = Admission.objects.filter(discharge_date__date=today).count() if hasattr(Admission, 'discharge_date') else 0
    pending_notes = NursingNote.objects.filter(created_at__date=today).count()
    total_notes = NursingNote.objects.count()

    # Popup data: admitted patient details
    admitted_list = Admission.objects.filter(status='admitted').select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')
    # Popup data: today admissions
    today_admission_list = Admission.objects.filter(admission_date__date=today).select_related('patient', 'doctor', 'ward', 'bed').order_by('-admission_date')
    # Popup data: recent notes
    recent_notes = NursingNote.objects.all().order_by('-created_at')[:20]

    # Chart data: admissions per day (last 7 days)
    from django.db.models import Count
    import datetime
    chart_days = []
    chart_counts = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_counts.append(Admission.objects.filter(admission_date__date=d).count())

    context = {
        'role': request.user.role,
        'assigned': assigned,
        'today_admissions': today_admissions,
        'today_discharges': today_discharges,
        'pending_notes': pending_notes,
        'total_notes': total_notes,
        'admitted_list': admitted_list,
        'today_admission_list': today_admission_list,
        'recent_notes': recent_notes,
        'chart_days': chart_days,
        'chart_counts': chart_counts,
    }
    return render(request, 'dashboard/nursing.html', context)


@login_required
@nursing_required
def add_nursing_note(request, patient_pk):
    """Add nursing note — observation, vitals, progress note. Cannot delete."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        note = NursingNote.objects.create(
            patient=patient,
            note_type=request.POST.get('note_type', 'nursing_note'),
            content=request.POST.get('content', ''),
            vital_bp=request.POST.get('vital_bp', ''),
            vital_temp=request.POST.get('vital_temp', ''),
            vital_pulse=request.POST.get('vital_pulse', ''),
            vital_resp=request.POST.get('vital_resp', ''),
            attached_file=request.FILES.get('attached_file'),
            created_by=request.user,
        )

        # Auto-attach to medical record
        MedicalRecord.objects.create(
            patient=patient, department='nursing',
            record_type='nursing_note',
            title=f'Nursing Note - {note.note_type}',
            summary=note.content,
            uploaded_by=str(request.user), staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action='Add Nursing Note', module='nursing',
            detail=f'{patient.patient_id} - {note.note_type}',
            patient_id=patient.patient_id,
        )
        return redirect(f'/nursing/patient/{patient_pk}/')

    context = {'patient': patient, 'role': request.user.role}
    return render(request, 'dashboard/nursing_note_form.html', context)


@login_required
@nursing_required
def nursing_patient_history(request, patient_pk):
    """View patient history — medical records, lab, radiology, doctor notes.
    Nursing can view but cannot edit/delete.
    """
    patient = get_object_or_404(Patient, pk=patient_pk)
    notes = NursingNote.objects.filter(patient=patient).order_by('-created_at')
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')[:20]
    lab_results = LabTestRequest.objects.filter(patient=patient).order_by('-created_at')[:10]
    radiology = RadiologyRequest.objects.filter(patient=patient).order_by('-created_at')[:10]

    context = {
        'patient': patient, 'notes': notes,
        'medical_records': medical_records, 'lab_results': lab_results,
        'radiology': radiology, 'role': request.user.role,
    }
    return render(request, 'dashboard/nursing_patient_history.html', context)
