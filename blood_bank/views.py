from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import BloodRequest
from patients.models import Patient
from medical_records.models import MedicalRecord
from accounts.decorators import blood_bank_required
from accounts.models import AuditLog


@login_required
@blood_bank_required
def blood_bank_dashboard(request):
    """Blood Bank Dashboard — blood requests, issued units, history, popup modals, charts."""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    pending = BloodRequest.objects.filter(status='pending').count()
    issued = BloodRequest.objects.filter(status='issued').count()
    completed = BloodRequest.objects.filter(status='completed').count()
    total = BloodRequest.objects.count()

    today_requests = BloodRequest.objects.filter(created_at__date=today).count()
    month_requests = BloodRequest.objects.filter(created_at__date__gte=month_start).count()

    recent_requests = BloodRequest.objects.all().order_by('-created_at')[:10]
    recent = BloodRequest.objects.all().order_by('-created_at')[:15]

    # Popup data
    pending_list = BloodRequest.objects.filter(status='pending').select_related('patient').order_by('-created_at')
    issued_list = BloodRequest.objects.filter(status='issued').select_related('patient').order_by('-created_at')
    completed_list = BloodRequest.objects.filter(status='completed', created_at__date__gte=month_start).select_related('patient').order_by('-created_at')

    # Group by blood group
    blood_stats = {}
    for bg in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']:
        blood_stats[bg] = BloodRequest.objects.filter(blood_group=bg, status='completed').aggregate(
            total=Sum('issued_units'))['total'] or 0

    # Chart data: requests by blood group
    chart_blood_groups = list(blood_stats.keys())
    chart_units = list(blood_stats.values())

    context = {
        'pending': pending, 'issued': issued, 'completed': completed,
        'total': total, 'today_requests': today_requests, 'month_requests': month_requests,
        'recent_requests': recent_requests, 'recent': recent,
        'blood_stats': blood_stats,
        'pending_list': pending_list,
        'issued_list': issued_list,
        'completed_list': completed_list,
        'chart_blood_groups': chart_blood_groups,
        'chart_units': chart_units,
        'role': request.user.role,
    }
    return render(request, 'dashboard/blood_bank.html', context)


@login_required
@blood_bank_required
def blood_request_detail(request, pk):
    """Blood request detail — issue blood, record notes."""
    blood_req = get_object_or_404(BloodRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'issue':
            blood_req.status = 'issued'
            blood_req.issued_units = request.POST.get('issued_units', 0)
            blood_req.notes = request.POST.get('notes', '')
            if request.FILES.get('issue_report'):
                blood_req.issue_report = request.FILES.get('issue_report')
            # Auto-attach to medical record
            MedicalRecord.objects.create(
                patient=blood_req.patient, department='blood_bank',
                record_type='blood_bank_record',
                title=f'Blood Issue - {blood_req.blood_group}',
                summary=f'Issued {blood_req.issued_units} units of {blood_req.blood_group}',
                uploaded_by=str(request.user), staff_name=str(request.user),
            )
        elif action == 'complete':
            blood_req.status = 'completed'
        blood_req.save()

        AuditLog.objects.create(
            user=request.user, action=f'Blood {action}', module='blood_bank',
            detail=f'{blood_req.blood_group} - {blood_req.patient.patient_id}',
            patient_id=blood_req.patient.patient_id,
        )
        return redirect('/blood-bank/')

    context = {'blood_req': blood_req, 'role': request.user.role}
    return render(request, 'dashboard/blood_request_detail.html', context)
