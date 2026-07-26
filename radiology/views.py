from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from consultations.models import RadiologyRequest
from radiology.models import RadiologyCatalog
from patients.models import Patient
from accounts.decorators import radiology_required, super_admin_required
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
@radiology_required
def radiology_dashboard(request):
    """Radiology Dashboard with stats, popup modals, and chart data."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    pending = RadiologyRequest.objects.filter(status='requested').count()
    scheduled = RadiologyRequest.objects.filter(status='scheduled').count()
    completed_today = RadiologyRequest.objects.filter(status='completed', created_at__date=today).count()
    completed_month = RadiologyRequest.objects.filter(status='completed', created_at__date__gte=month_start).count()
    completed_year = RadiologyRequest.objects.filter(status='completed', created_at__date__gte=year_start).count()
    total = RadiologyRequest.objects.count()

    # Popup data
    pending_list = RadiologyRequest.objects.filter(status='requested').select_related('patient').order_by('created_at')[:30]
    scheduled_list = RadiologyRequest.objects.filter(status='scheduled').select_related('patient').order_by('created_at')[:30]
    completed_today_list = RadiologyRequest.objects.filter(status='completed', created_at__date=today).select_related('patient').order_by('-completed_at')[:30]
    completed_month_list = RadiologyRequest.objects.filter(status='completed', created_at__date__gte=month_start).select_related('patient').order_by('-completed_at')[:30]

    # Chart data: scans per day (last 7 days)
    import datetime
    chart_days = []
    chart_completed = []
    chart_new = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_completed.append(RadiologyRequest.objects.filter(status='completed', created_at__date=d).count())
        chart_new.append(RadiologyRequest.objects.filter(created_at__date=d).count())

    context = {
        'pending': pending, 'scheduled': scheduled,
        'completed_today': completed_today,
        'completed_month': completed_month,
        'completed_year': completed_year,
        'total': total,
        'pending_list': pending_list,
        'scheduled_list': scheduled_list,
        'completed_today_list': completed_today_list,
        'completed_month_list': completed_month_list,
        'chart_days': chart_days,
        'chart_completed': chart_completed,
        'chart_new': chart_new,
        'role': request.user.role,
    }
    return render(request, 'dashboard/radiology.html', context)


@login_required
@radiology_required
def radiology_queue(request):
    """Radiology queue — pending and scheduled requests."""
    pending = RadiologyRequest.objects.filter(status='requested').order_by('created_at')
    scheduled = RadiologyRequest.objects.filter(status='scheduled').order_by('created_at')
    completed = RadiologyRequest.objects.filter(status='completed').order_by('-completed_at')[:20]
    context = {
        'pending': pending, 'scheduled': scheduled, 'completed': completed,
        'role': request.user.role,
    }
    return render(request, 'dashboard/radiology_queue.html', context)


@login_required
@radiology_required
def radiology_request_detail(request, pk):
    """Radiology request detail — upload result, change status."""
    rad_request = get_object_or_404(RadiologyRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'schedule':
            rad_request.status = 'scheduled'
        elif action == 'start':
            rad_request.status = 'in_progress'
        elif action == 'complete':
            rad_request.status = 'completed'
            rad_request.completed_at = timezone.now()
            rad_request.findings = request.POST.get('findings', '')
            rad_request.impression = request.POST.get('impression', '')
            rad_request.result_notes = request.POST.get('result_notes', '')
            if request.FILES.get('result_file'):
                rad_request.result_file = request.FILES.get('result_file')
            # Auto-attach to medical record
            MedicalRecord.objects.create(
                patient=rad_request.patient, department='radiology',
                record_type='radiology_report',
                title=f'Radiology Report - {rad_request.imaging_type}',
                summary=rad_request.findings,
                file=rad_request.result_file if rad_request.result_file else None,
                uploaded_by=str(request.user), staff_name=str(request.user),
            )
        rad_request.save()
        AuditLog.objects.create(
            user=request.user, action=f'Radiology {action}', module='radiology',
            detail=f'{rad_request.request_id}', patient_id=rad_request.patient.patient_id,
        )
        return redirect('/radiology/queue/')

    context = {'rad_request': rad_request, 'role': request.user.role}
    return render(request, 'dashboard/radiology_request_detail.html', context)


@login_required
def radiology_search(request):
    """Search radiology requests."""
    query = request.GET.get('q', '')
    results = RadiologyRequest.objects.all().order_by('-created_at')
    if query:
        results = results.filter(
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(request_id__icontains=query)
        )
    return render(request, 'dashboard/radiology_search.html', {
        'results': results, 'query': query, 'role': request.user.role,
    })


@login_required
def radiology_report_pdf(request, pk):
    """Download radiology report as PDF."""
    rad = get_object_or_404(RadiologyRequest, pk=pk)
    context = {'rad_request': rad, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/radiology_request_detail.html', context,
                           filename=f'RadiologyReport-{rad.patient.patient_id}.pdf')


@login_required
def radiology_report_jpg(request, pk):
    """Download radiology report as JPG."""
    rad = get_object_or_404(RadiologyRequest, pk=pk)
    context = {'rad_request': rad, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/radiology_request_detail.html', context,
                              filename=f'RadiologyReport-{rad.patient.patient_id}.jpg')


@login_required
@super_admin_required
def radiology_catalog_list(request):
    """Manage radiology catalog — Super Admin only."""
    catalogs = RadiologyCatalog.objects.all().order_by('code')
    return render(request, 'dashboard/radiology_catalog_list.html', {
        'catalogs': catalogs, 'role': 'super_admin',
    })


@login_required
@super_admin_required
def radiology_catalog_add(request):
    """Add radiology test to catalog — Super Admin only."""
    if request.method == 'POST':
        RadiologyCatalog.objects.create(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            price=request.POST.get('price', 0),
            imaging_type=request.POST.get('imaging_type'),
        )
        return redirect('/radiology/catalog/')
    return render(request, 'dashboard/radiology_catalog_form.html', {
        'role': 'super_admin',
    })
