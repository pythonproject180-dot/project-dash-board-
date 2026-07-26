from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import User, AuditLog
from .decorators import super_admin_required


def login_view(request):
    """Staff login page — Dasher template design."""
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active and user.is_active_staff:
            login(request, user)
            AuditLog.objects.create(user=user, action='Login', module='accounts', detail=f'Role: {user.role}')
            return redirect(user.get_dashboard_url())
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials or account disabled'})
    return render(request, 'accounts/login.html')


@login_required
def login_success(request):
    return redirect(request.user.get_dashboard_url())


def logout_view(request):
    """Logout with audit log."""
    if request.user.is_authenticated:
        AuditLog.objects.create(user=request.user, action='Logout', module='accounts')
    logout(request)
    return redirect('/accounts/login/')


@login_required
@super_admin_required
def super_admin_dashboard(request):
    """Super Admin Dashboard — full overview with stats, audit logs, Django Admin link."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    from patients.models import Patient
    from billing.models import Bill
    from admissions.models import Admission
    from doctors.models import Doctor
    from departments.models import Department
    from insurance.models import InsuranceClaim

    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_departments = Department.objects.count()
    total_bills = Bill.objects.count()
    total_admissions = Admission.objects.filter(status='admitted').count()
    total_users = User.objects.filter(is_active_staff=True).count()
    total_claims = InsuranceClaim.objects.count()

    today_collection = Bill.objects.filter(created_at__date=today).aggregate(total=Sum('net_amount'))['total'] or 0
    month_collection = Bill.objects.filter(created_at__date__gte=month_start).aggregate(total=Sum('net_amount'))['total'] or 0
    year_collection = Bill.objects.filter(created_at__date__gte=year_start).aggregate(total=Sum('net_amount'))['total'] or 0

    recent_logs = AuditLog.objects.all()[:20]

    # Popup data for stat cards
    today_bills_list = Bill.objects.filter(created_at__date=today).select_related('patient').order_by('-created_at')[:30]
    today_patients_list = Patient.objects.filter(created_at__date=today).order_by('-created_at')[:30]
    month_patients_list = Patient.objects.filter(created_at__date__gte=month_start).order_by('-created_at')[:30]

    # Chart data: revenue per day (last 7 days)
    import datetime
    chart_days = []
    chart_revenue = []
    chart_registrations = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_revenue.append(float(Bill.objects.filter(created_at__date=d).aggregate(total=Sum('net_amount'))['total'] or 0))
        chart_registrations.append(Patient.objects.filter(created_at__date=d).count())

    def fmt(amount):
        try:
            amt = float(amount)
            if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
            elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
            else: return f'NPR {amt:,.0f}'
        except: return f'NPR {amount}'

    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_departments': total_departments,
        'total_bills': total_bills,
        'total_admissions': total_admissions,
        'total_users': total_users,
        'total_claims': total_claims,
        'today_collection': fmt(today_collection),
        'today_collection_raw': today_collection,
        'month_collection': fmt(month_collection),
        'month_collection_raw': month_collection,
        'year_collection': fmt(year_collection),
        'year_collection_raw': year_collection,
        'recent_logs': recent_logs,
        'today_bills_list': today_bills_list,
        'today_patients_list': today_patients_list,
        'month_patients_list': month_patients_list,
        'chart_days': chart_days,
        'chart_revenue': chart_revenue,
        'chart_registrations': chart_registrations,
        'role': 'super_admin',
        'has_django_admin': True,
    }
    return render(request, 'dashboard/super_admin.html', context)


@login_required
@super_admin_required
def staff_list(request):
    """Staff list — Super Admin only."""
    staff = User.objects.filter(is_active_staff=True)
    return render(request, 'dashboard/staff_list.html', {'staff': staff, 'role': 'super_admin'})


@login_required
@super_admin_required
def add_staff(request):
    """Add staff — Super Admin only."""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        user = User.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            role=role, phone=phone, is_staff=True, is_active_staff=True,
        )
        AuditLog.objects.create(user=request.user, action='Create Staff', module='accounts',
                                detail=f'Created {role}: {username}')
        return redirect('/accounts/staff/')
    return render(request, 'dashboard/add_staff.html', {'role': 'super_admin'})
