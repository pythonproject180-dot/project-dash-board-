from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count
from .models import Insurer, PatientInsurance, InsuranceClaim
from patients.models import Patient
from accounts.decorators import insurance_required, super_admin_required
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
@insurance_required
def insurance_dashboard(request):
    """Insurance Dashboard — Nepal Government + Private insurance support, popup modals, charts."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    pending_claims = InsuranceClaim.objects.filter(status='pending').count()
    approved_claims = InsuranceClaim.objects.filter(status='approved').count()
    rejected_claims = InsuranceClaim.objects.filter(status='rejected').count()
    settled_claims = InsuranceClaim.objects.filter(status='settled').count()
    total_claims = InsuranceClaim.objects.count()

    today_amount = InsuranceClaim.objects.filter(created_at__date=today, status='approved').aggregate(total=Sum('approved_amount'))['total'] or 0
    month_amount = InsuranceClaim.objects.filter(created_at__date__gte=month_start, status='approved').aggregate(total=Sum('approved_amount'))['total'] or 0

    # Popup data
    recent_claims = InsuranceClaim.objects.all().select_related('patient', 'insurance').order_by('-created_at')[:20]
    pending_list = InsuranceClaim.objects.filter(status='pending').select_related('patient', 'insurance').order_by('-created_at')[:30]
    approved_list = InsuranceClaim.objects.filter(status='approved').select_related('patient', 'insurance').order_by('-created_at')[:30]
    settled_list = InsuranceClaim.objects.filter(status='settled').select_related('patient', 'insurance').order_by('-created_at')[:30]

    # Chart data: claims per day (last 7 days)
    import datetime
    chart_days = []
    chart_approved = []
    chart_submitted = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        chart_approved.append(InsuranceClaim.objects.filter(status='approved', created_at__date=d).count())
        chart_submitted.append(InsuranceClaim.objects.filter(created_at__date=d).count())

    context = {
        'pending_claims': pending_claims, 'approved_claims': approved_claims,
        'rejected_claims': rejected_claims, 'settled_claims': settled_claims,
        'total_claims': total_claims,
        'today_amount': fmt(today_amount), 'month_amount': fmt(month_amount),
        'recent_claims': recent_claims,
        'pending_list': pending_list,
        'approved_list': approved_list,
        'settled_list': settled_list,
        'chart_days': chart_days,
        'chart_approved': chart_approved,
        'chart_submitted': chart_submitted,
        'role': request.user.role,
    }
    return render(request, 'dashboard/insurance.html', context)


@login_required
def insurer_list(request):
    """Insurer list."""
    insurers = Insurer.objects.filter(is_active=True)
    return render(request, 'dashboard/insurer_list.html', {'insurers': insurers, 'role': request.user.role})


@login_required
@super_admin_required
def insurer_add(request):
    """Add insurer — Super Admin only."""
    if request.method == 'POST':
        Insurer.objects.create(
            name=request.POST.get('name'),
            code=request.POST.get('code'),
            address=request.POST.get('address', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
        )
        return redirect('/insurance/insurers/')
    return render(request, 'dashboard/insurer_form.html', {'role': 'super_admin'})


@login_required
@insurance_required
def claim_submit(request):
    """Submit insurance claim — QR scan or manual insurance number entry.
    Workflow: Scan QR / Enter Insurance Number → Retrieve Insurance → Approve Claim →
    Calculate Discount → Generate Insurance Receipt → Save to Medical Record.
    """
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        insurance_id = request.POST.get('insurance')
        amount = request.POST.get('amount', 0)
        notes = request.POST.get('notes', '')

        patient = get_object_or_404(Patient, pk=patient_id)
        insurance = get_object_or_404(PatientInsurance, pk=insurance_id) if insurance_id else None

        # Calculate discount based on coverage percentage
        discount_amount = 0
        if insurance and insurance.coverage_percentage:
            discount_amount = float(amount) * (float(insurance.coverage_percentage) / 100)

        claim = InsuranceClaim.objects.create(
            patient=patient,
            insurance=insurance,
            amount=amount,
            approved_amount=0,
            notes=notes,
            submitted_by=request.user,
        )

        AuditLog.objects.create(
            user=request.user, action='Submit Insurance Claim', module='insurance',
            detail=f'{claim.claim_id} - NPR {amount}', patient_id=patient.patient_id,
        )
        return redirect(f'/insurance/claim/{claim.pk}/')

    patients = Patient.objects.all().order_by('-created_at')
    insurers = Insurer.objects.filter(is_active=True)
    insurances = PatientInsurance.objects.filter(is_active=True)
    return render(request, 'dashboard/claim_form.html', {
        'patients': patients, 'insurers': insurers, 'insurances': insurances,
        'role': request.user.role,
    })


@login_required
@insurance_required
def claim_review(request, pk):
    """Review and approve/reject insurance claim.
    Approve → Calculate discount → Generate receipt with QR + barcodes.
    Receipt contains: Patient Info, Insurance Number, Patient QR, Insurance QR,
    Services, Discount, Amount Paid, Remaining Balance.
    """
    claim = get_object_or_404(InsuranceClaim, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            approved_amount = request.POST.get('approved_amount', 0)
            claim.approved_amount = approved_amount
            claim.status = 'approved'
            claim.processed_at = timezone.now()
        elif action == 'reject':
            claim.status = 'rejected'
            claim.processed_at = timezone.now()
        elif action == 'settle':
            claim.status = 'settled'
            claim.processed_at = timezone.now()
        claim.notes += '\n' + request.POST.get('review_notes', '')
        claim.save()

        # Auto-attach to medical record
        MedicalRecord.objects.create(
            patient=claim.patient, department='insurance',
            record_type='insurance_doc',
            title=f'Insurance Claim - {claim.claim_id}',
            summary=f'Status: {claim.status}. Amount: NPR {claim.amount}. Approved: NPR {claim.approved_amount}',
            uploaded_by=str(request.user), staff_name=str(request.user),
        )

        AuditLog.objects.create(
            user=request.user, action=f'Insurance {action}', module='insurance',
            detail=f'{claim.claim_id}', patient_id=claim.patient.patient_id,
        )
        return redirect('/insurance/')

    insurance = claim.insurance
    coverage_pct = float(insurance.coverage_percentage) if insurance and insurance.coverage_percentage else 0
    discount_amount = float(claim.amount) * (coverage_pct / 100)
    remaining = float(claim.amount) - discount_amount

    context = {
        'claim': claim, 'insurance': insurance,
        'coverage_pct': coverage_pct, 'discount_amount': fmt(discount_amount),
        'remaining': fmt(remaining),
        'role': request.user.role,
    }
    return render(request, 'dashboard/claim_review.html', context)


@login_required
def claim_receipt_pdf(request, pk):
    """Download insurance claim receipt as PDF."""
    claim = get_object_or_404(InsuranceClaim, pk=pk)
    insurance = claim.insurance
    coverage_pct = float(insurance.coverage_percentage) if insurance and insurance.coverage_percentage else 0
    discount_amount = float(claim.amount) * (coverage_pct / 100)
    remaining = float(claim.amount) - discount_amount
    context = {
        'claim': claim, 'insurance': insurance,
        'coverage_pct': coverage_pct, 'discount_amount': discount_amount,
        'remaining': remaining, 'role': request.user.role, 'is_pdf': True,
    }
    return download_as_pdf('dashboard/claim_receipt.html', context, filename=f'Insurance-{claim.claim_id}.pdf')


@login_required
def claim_receipt_jpg(request, pk):
    """Download insurance claim receipt as JPG."""
    claim = get_object_or_404(InsuranceClaim, pk=pk)
    insurance = claim.insurance
    coverage_pct = float(insurance.coverage_percentage) if insurance and insurance.coverage_percentage else 0
    discount_amount = float(claim.amount) * (coverage_pct / 100)
    remaining = float(claim.amount) - discount_amount
    context = {
        'claim': claim, 'insurance': insurance,
        'coverage_pct': coverage_pct, 'discount_amount': discount_amount,
        'remaining': remaining, 'role': request.user.role, 'is_pdf': True,
    }
    return download_as_image('dashboard/claim_receipt.html', context, filename=f'Insurance-{claim.claim_id}.jpg')


@login_required
def claims_report(request):
    """Insurance claims report — filter by date, status, insurer."""
    today = timezone.now().date()
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')

    claims = InsuranceClaim.objects.all().order_by('-created_at')
    if date_filter:
        claims = claims.filter(created_at__date=date_filter)
    if status_filter:
        claims = claims.filter(status=status_filter)

    total = claims.aggregate(total=Sum('amount'))['total'] or 0
    approved = claims.filter(status='approved').aggregate(total=Sum('approved_amount'))['total'] or 0

    context = {
        'claims': claims, 'total': fmt(total), 'approved': fmt(approved),
        'date_filter': date_filter, 'status_filter': status_filter,
        'role': request.user.role,
    }
    return render(request, 'dashboard/claims_report.html', context)
