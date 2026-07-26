from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from billing.models import Bill, HospitalService, BillItem
from patients.models import Patient, OPDVisit
from admissions.models import Admission
from pharmacy.models import PharmacySale
from consultations.models import LabTestRequest, RadiologyRequest
from insurance.models import InsuranceClaim
from accounts.decorators import accounts_required, super_admin_required
import csv


def fmt(amount):
    try:
        amt = float(amount)
        if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
        else: return f'NPR {amt:,.0f}'
    except: return f'NPR {amount}'


@login_required
def revenue_csv_export(request):
    """CSV export for revenue data."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="revenue_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Bill ID', 'Patient', 'Date', 'Total Amount', 'Discount', 'Net Amount', 'Payment Method', 'Status'])
    for bill in Bill.objects.all().order_by('-created_at'):
        writer.writerow([bill.bill_id, bill.patient.full_name, bill.created_at.strftime('%Y-%m-%d'),
                         bill.total_amount, bill.discount_amount, bill.net_amount, bill.payment_method, 'Paid' if bill.paid else 'Unpaid'])
    return response


@login_required
def revenue_dashboard(request):
    """Revenue dashboard — total collection stats."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    today_rev = Bill.objects.filter(created_at__date=today).aggregate(total=Sum('net_amount'))['total'] or 0
    month_rev = Bill.objects.filter(created_at__date__gte=month_start).aggregate(total=Sum('net_amount'))['total'] or 0
    year_rev = Bill.objects.filter(created_at__date__gte=year_start).aggregate(total=Sum('net_amount'))['total'] or 0

    context = {
        'today_revenue': fmt(today_rev), 'month_revenue': fmt(month_rev),
        'year_revenue': fmt(year_rev), 'role': request.user.role,
    }
    return render(request, 'dashboard/revenue.html', context)


@login_required
@accounts_required
def accounts_dashboard(request):
    """Accounts Dashboard — department-wise revenue breakdown with drill-down.
    Registration Revenue, Laboratory Revenue, Radiology Revenue,
    Pharmacy Revenue, Admission Revenue, Insurance Revenue, Grand Total.
    Click department → view all transactions via modal.
    """
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Department-wise collection
    dept_revenues = {}
    dept_revenues['Registration'] = OPDVisit.objects.filter(visit_date__date__gte=month_start).aggregate(total=Sum('registration_fee'))['total'] or 0
    dept_revenues['Laboratory'] = LabTestRequest.objects.filter(created_at__date__gte=month_start).count() * 300  # avg lab test price
    dept_revenues['Radiology'] = RadiologyRequest.objects.filter(created_at__date__gte=month_start).count() * 500
    dept_revenues['Pharmacy'] = PharmacySale.objects.filter(sale_date__date__gte=month_start).aggregate(total=Sum('final_amount'))['total'] or 0
    dept_revenues['Admission'] = Admission.objects.filter(admission_date__date__gte=month_start).aggregate(total=Sum('admission_fee'))['total'] or 0
    dept_revenues['Insurance'] = InsuranceClaim.objects.filter(created_at__date__gte=month_start, status='approved').aggregate(total=Sum('approved_amount'))['total'] or 0
    dept_revenues['Cash Counter'] = Bill.objects.filter(created_at__date__gte=month_start).aggregate(total=Sum('net_amount'))['total'] or 0

    grand_total = sum(dept_revenues.values())

    # Drill-down data for modal popups
    cash_bills = Bill.objects.filter(created_at__date__gte=month_start).order_by('-created_at')[:20]
    reg_visits = OPDVisit.objects.filter(visit_date__date__gte=month_start).order_by('-visit_date')[:20]
    pharm_sales = PharmacySale.objects.filter(sale_date__date__gte=month_start).order_by('-sale_date')[:20]

    # Chart data: daily revenue (last 7 days)
    import datetime
    chart_days = []
    chart_revenue = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_revenue.append(float(Bill.objects.filter(created_at__date=d).aggregate(total=Sum('net_amount'))['total'] or 0))

    context = {
        'dept_revenues': dept_revenues,
        'grand_total': fmt(grand_total),
        'grand_total_raw': grand_total,
        'today': today, 'month_start': month_start,
        'cash_bills': cash_bills,
        'reg_visits': reg_visits,
        'pharm_sales': pharm_sales,
        'chart_days': chart_days,
        'chart_revenue': chart_revenue,
        'role': request.user.role,
    }
    return render(request, 'dashboard/accounts.html', context)


@login_required
def registration_report(request):
    """Registration report — daily, monthly, yearly registrations."""
    today = timezone.now().date()
    today_reg = Patient.objects.filter(created_at__date=today).count()
    month_reg = Patient.objects.filter(created_at__date__gte=today.replace(day=1)).count()
    year_reg = Patient.objects.filter(created_at__date__gte=today.replace(month=1, day=1)).count()

    context = {
        'today_reg': today_reg, 'month_reg': month_reg, 'year_reg': year_reg,
        'role': request.user.role,
    }
    return render(request, 'dashboard/registration_report.html', context)


@login_required
def department_report(request):
    """Department-wise report."""
    from departments.models import Department
    departments = Department.objects.annotate(
        patient_count=Count('opdvisit', filter=Q(opdvisit__visit_date__date__gte=timezone.now().date().replace(day=1))),
    )
    context = {'departments': departments, 'role': request.user.role}
    return render(request, 'dashboard/department_report.html', context)


@login_required
def doctor_report(request):
    """Doctor-wise report — patients seen, revenue generated."""
    from doctors.models import Doctor
    doctors = Doctor.objects.annotate(
        visits=Count('opdvisit', filter=Q(opdvisit__status='completed')),
    )
    context = {'doctors': doctors, 'role': request.user.role}
    return render(request, 'dashboard/doctor_report.html', context)


@login_required
def pharmacy_report(request):
    """Pharmacy report — sales, revenue, stock status."""
    today = timezone.now().date()
    today_sales = PharmacySale.objects.filter(sale_date__date=today).aggregate(total=Sum('final_amount'))['total'] or 0
    total_medicines = PharmacySale.objects.count()

    context = {
        'today_sales': fmt(today_sales), 'total_sales': total_medicines,
        'role': request.user.role,
    }
    return render(request, 'dashboard/pharmacy_report.html', context)


@login_required
def lab_report(request):
    """Lab report — tests completed, revenue."""
    today = timezone.now().date()
    completed = LabTestRequest.objects.filter(status='completed').count()
    pending = LabTestRequest.objects.filter(status='pending').count()

    context = {
        'completed': completed, 'pending': pending,
        'role': request.user.role,
    }
    return render(request, 'dashboard/lab_report.html', context)
