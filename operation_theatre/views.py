from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Surgery
from patients.models import Patient
from consultations.models import LabTestRequest, RadiologyRequest
from medical_records.models import MedicalRecord
from accounts.decorators import ot_required
from accounts.models import AuditLog


@login_required
@ot_required
def ot_dashboard(request):
    """Operation Theatre Dashboard — surgery schedule, stats."""
    from django.utils import timezone
    today = timezone.now().date()
    scheduled = Surgery.objects.filter(status='scheduled').count()
    in_progress = Surgery.objects.filter(status='in_progress').count()
    completed_today = Surgery.objects.filter(status='completed', created_at__date=today).count()
    total = Surgery.objects.count()

    upcoming = Surgery.objects.filter(status='scheduled').order_by('planned_date')[:10]
    recent_completed = Surgery.objects.filter(status='completed').order_by('-completed_at')[:10]

    context = {
        'scheduled': scheduled, 'in_progress': in_progress,
        'completed_today': completed_today, 'total': total,
        'upcoming': upcoming, 'recent_completed': recent_completed,
        'role': request.user.role,
    }
    return render(request, 'dashboard/operation_theatre.html', context)


@login_required
@ot_required
def surgery_detail(request, pk):
    """Surgery detail — access complete patient history, add operation notes, upload OT reports."""
    surgery = get_object_or_404(Surgery, pk=pk)
    patient = surgery.patient

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'start':
            surgery.status = 'in_progress'
        elif action == 'complete':
            surgery.status = 'completed'
            surgery.completed_at = timezone.now()
            surgery.operative_report = request.POST.get('operative_report', '')
            surgery.surgical_notes = request.POST.get('surgical_notes', '')
            surgery.procedure_summary = request.POST.get('procedure_summary', '')
            if request.FILES.get('result_file'):
                surgery.result_file = request.FILES.get('result_file')
            # Auto-attach to medical record
            MedicalRecord.objects.create(
                patient=patient, department='operation_theatre',
                record_type='ot_record',
                title=f'Surgery Report - {surgery.surgery_type}',
                summary=surgery.procedure_summary,
                uploaded_by=str(request.user), staff_name=str(request.user),
            )
        elif action == 'cancel':
            surgery.status = 'cancelled'
        surgery.save()

        AuditLog.objects.create(
            user=request.user, action=f'OT {action}', module='operation_theatre',
            detail=f'{surgery.surgery_type} - {patient.patient_id}',
            patient_id=patient.patient_id,
        )
        return redirect('/operation-theatre/')

    # Patient history data
    lab_results = LabTestRequest.objects.filter(patient=patient).order_by('-created_at')[:10]
    radiology = RadiologyRequest.objects.filter(patient=patient).order_by('-created_at')[:10]
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')[:20]

    context = {
        'surgery': surgery, 'patient': patient,
        'lab_results': lab_results, 'radiology': radiology,
        'medical_records': medical_records,
        'role': request.user.role,
    }
    return render(request, 'dashboard/surgery_detail.html', context)
