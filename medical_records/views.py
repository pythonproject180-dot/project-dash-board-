from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import MedicalRecord
from patients.models import Patient
from accounts.decorators import medical_records_required, super_admin_required


@login_required
@medical_records_required
def medical_records_dashboard(request):
    """Medical Records Dashboard — centralized repository with popup modals and chart data."""
    total_records = MedicalRecord.objects.count()
    recent_records = MedicalRecord.objects.all().order_by('-created_at')[:20]
    recent = recent_records

    # Stats by type
    type_stats = {}
    type_labels = {'doctor_note': 'Doctor Notes', 'nursing_note': 'Nursing Notes',
                   'lab_report': 'Lab Reports', 'radiology_report': 'Radiology Reports',
                   'pharmacy_record': 'Pharmacy Records', 'blood_bank_record': 'Blood Bank Records',
                   'admission_record': 'Admission Records', 'ot_record': 'OT Records',
                   'insurance_doc': 'Insurance Docs', 'uploaded_pdf': 'Uploaded PDFs'}
    for rtype in type_labels.keys():
        type_stats[rtype] = MedicalRecord.objects.filter(record_type=rtype).count()

    # Popup data: records by type
    doctor_notes = MedicalRecord.objects.filter(record_type='doctor_note').order_by('-created_at')[:20]
    lab_reports = MedicalRecord.objects.filter(record_type='lab_report').order_by('-created_at')[:20]
    radiology_reports = MedicalRecord.objects.filter(record_type='radiology_report').order_by('-created_at')[:20]

    # Chart data: records by type distribution
    chart_types = list(type_labels.values())
    chart_counts = list(type_stats.values())

    context = {
        'total_records': total_records, 'recent_records': recent_records,
        'recent': recent, 'type_stats': type_stats, 'type_labels': type_labels,
        'doctor_notes': doctor_notes,
        'lab_reports': lab_reports,
        'radiology_reports': radiology_reports,
        'chart_types': chart_types,
        'chart_counts': chart_counts,
        'role': request.user.role,
    }
    return render(request, 'dashboard/medical_records.html', context)


@login_required
def patient_records(request, patient_pk):
    """View patient's medical records — chronological timeline.
    Access: Doctor, Registration, Nursing, OT, Blood Bank, Admission, Insurance, Pharmacy, Super Admin, Medical Records.
    Only Super Admin can edit.
    """
    patient = get_object_or_404(Patient, pk=patient_pk)
    records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')
    can_edit = request.user.role == 'super_admin' or request.user.is_superuser

    context = {
        'patient': patient, 'records': records, 'can_edit': can_edit,
        'role': request.user.role,
    }
    return render(request, 'dashboard/patient_records.html', context)


@login_required
def search_records(request):
    """Search medical records by patient ID, type, department."""
    query = request.GET.get('q', '')
    type_filter = request.GET.get('type', '')
    records = MedicalRecord.objects.all().order_by('-created_at')
    if query:
        records = records.filter(
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(title__icontains=query)
        )
    if type_filter:
        records = records.filter(record_type=type_filter)
    return render(request, 'dashboard/records_search.html', {
        'records': records, 'query': query, 'type_filter': type_filter,
        'role': request.user.role,
    })


@login_required
@super_admin_required
def upload_record(request, patient_pk):
    """Upload medical record — only Super Admin can edit/upload directly."""
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        MedicalRecord.objects.create(
            patient=patient,
            department=request.POST.get('department', 'admin'),
            record_type=request.POST.get('record_type', 'uploaded_pdf'),
            title=request.POST.get('title', ''),
            summary=request.POST.get('summary', ''),
            file=request.FILES.get('file'),
            uploaded_by=str(request.user),
            staff_name=str(request.user),
        )
        return redirect(f'/medical-records/patient/{patient_pk}/')

    context = {'patient': patient, 'role': 'super_admin'}
    return render(request, 'dashboard/upload_record.html', context)
