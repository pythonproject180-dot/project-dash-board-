from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from consultations.models import LabTestRequest
from laboratory.models import LabCatalog
from patients.models import Patient
from accounts.decorators import laboratory_required, super_admin_required
from accounts.models import AuditLog
from medical_records.models import MedicalRecord
from utils.pdf_utils import download_as_pdf, download_as_image


def fmt(amount):
    try:
        amt = float(amount)
        if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
        else: return f'NPR {amt:,.0f}'
    except: return f'NPR {amount}'


@login_required
@laboratory_required
def lab_dashboard(request):
    """Lab Dashboard with stats, popup modals, and chart data."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    pending = LabTestRequest.objects.filter(status='pending').count()
    testing = LabTestRequest.objects.filter(status='testing').count()
    completed_today = LabTestRequest.objects.filter(status='completed', created_at__date=today).count()
    completed_month = LabTestRequest.objects.filter(status='completed', created_at__date__gte=month_start).count()
    completed_year = LabTestRequest.objects.filter(status='completed', created_at__date__gte=year_start).count()
    total_requests = LabTestRequest.objects.count()

    # Popup data
    pending_list = LabTestRequest.objects.filter(status='pending').select_related('patient').order_by('created_at')[:30]
    testing_list = LabTestRequest.objects.filter(status='testing').select_related('patient').order_by('created_at')[:30]
    completed_today_list = LabTestRequest.objects.filter(status='completed', created_at__date=today).select_related('patient').order_by('-completed_at')[:30]
    completed_month_list = LabTestRequest.objects.filter(status='completed', created_at__date__gte=month_start).select_related('patient').order_by('-completed_at')[:30]

    # Chart data: tests per day (last 7 days)
    import datetime
    chart_days = []
    chart_completed = []
    chart_new = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_completed.append(LabTestRequest.objects.filter(status='completed', created_at__date=d).count())
        chart_new.append(LabTestRequest.objects.filter(created_at__date=d).count())

    context = {
        'pending': pending, 'testing': testing,
        'completed_today': completed_today,
        'completed_month': completed_month,
        'completed_year': completed_year,
        'total_requests': total_requests,
        'pending_list': pending_list,
        'testing_list': testing_list,
        'completed_today_list': completed_today_list,
        'completed_month_list': completed_month_list,
        'chart_days': chart_days,
        'chart_completed': chart_completed,
        'chart_new': chart_new,
        'role': request.user.role,
    }
    return render(request, 'dashboard/laboratory.html', context)


@login_required
@laboratory_required
def lab_queue(request):
    """Lab queue — pending and testing requests."""
    pending = LabTestRequest.objects.filter(status='pending').order_by('created_at')
    testing = LabTestRequest.objects.filter(status='testing').order_by('created_at')
    completed = LabTestRequest.objects.filter(status='completed').order_by('-completed_at')[:20]
    context = {
        'pending': pending, 'testing': testing, 'completed': completed,
        'role': request.user.role,
    }
    return render(request, 'dashboard/lab_queue.html', context)


@login_required
@laboratory_required
def lab_request_detail(request, pk):
    """Lab request detail — upload result PDF/scan, change status."""
    lab_request = get_object_or_404(LabTestRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            lab_request.status = 'accepted'
        elif action == 'collect_sample':
            lab_request.status = 'sample_collected'
        elif action == 'start_testing':
            lab_request.status = 'testing'
        elif action == 'complete':
            lab_request.status = 'completed'
            lab_request.completed_at = timezone.now()
            lab_request.result_notes = request.POST.get('result_notes', '')
            if request.FILES.get('result_file'):
                lab_request.result_file = request.FILES.get('result_file')
            # Auto-attach to medical record
            MedicalRecord.objects.create(
                patient=lab_request.patient, department='laboratory',
                record_type='lab_report',
                title=f'Lab Report - {lab_request.test_name}',
                summary=lab_request.result_notes,
                file=lab_request.result_file if lab_request.result_file else None,
                uploaded_by=str(request.user), staff_name=str(request.user),
            )
        lab_request.save()
        AuditLog.objects.create(
            user=request.user, action=f'Lab {action}', module='laboratory',
            detail=f'{lab_request.test_name}', patient_id=lab_request.patient.patient_id,
        )
        return redirect('/laboratory/queue/')

    context = {'lab_request': lab_request, 'role': request.user.role}
    return render(request, 'dashboard/lab_request_detail.html', context)


@login_required
def lab_search(request):
    """Search lab requests by Hospital ID, Name, Phone."""
    query = request.GET.get('q', '')
    results = LabTestRequest.objects.all().order_by('-created_at')
    if query:
        results = results.filter(
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(test_name__icontains=query)
        )
    return render(request, 'dashboard/lab_search.html', {
        'results': results, 'query': query, 'role': request.user.role,
    })


@login_required
def lab_report_pdf(request, pk):
    """Download lab report as PDF."""
    lab = get_object_or_404(LabTestRequest, pk=pk)
    context = {'lab_request': lab, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/lab_request_detail.html', context,
                           filename=f'LabReport-{lab.patient.patient_id}.pdf')


@login_required
def lab_report_jpg(request, pk):
    """Download lab report as JPG."""
    lab = get_object_or_404(LabTestRequest, pk=pk)
    context = {'lab_request': lab, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/lab_request_detail.html', context,
                              filename=f'LabReport-{lab.patient.patient_id}.jpg')


@login_required
@super_admin_required
def lab_catalog_list(request):
    """Manage lab test catalog — Super Admin only."""
    catalogs = LabCatalog.objects.all().order_by('code')
    return render(request, 'dashboard/lab_catalog_list.html', {
        'catalogs': catalogs, 'role': 'super_admin',
    })


@login_required
@super_admin_required
def lab_catalog_add(request):
    """Add lab test to catalog — Super Admin only."""
    from departments.models import Department
    if request.method == 'POST':
        LabCatalog.objects.create(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            price=request.POST.get('price', 0),
            department_id=request.POST.get('department'),
        )
        return redirect('/laboratory/catalog/')
    departments = Department.objects.filter(is_active=True)
    return render(request, 'dashboard/lab_catalog_form.html', {
        'departments': departments, 'role': 'super_admin',
    })


@login_required
def lab_csv_export(request):
    """CSV export for laboratory data."""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lab_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Request ID', 'Patient', 'Hospital ID', 'Test Name', 'Priority', 'Status', 'Result Notes', 'Date'])
    for req in LabTestRequest.objects.all().order_by('-created_at'):
        writer.writerow([req.pk, req.patient.full_name, req.patient.patient_id,
                         req.test_name, req.priority, req.status,
                         req.result_notes, req.created_at.strftime('%Y-%m-%d')])
    return response
