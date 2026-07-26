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
    """Nursing Dashboard — search patient, view medical records, add notes."""
    context = {'role': request.user.role}
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
