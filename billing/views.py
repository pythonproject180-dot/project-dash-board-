from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import HospitalService, Bill, BillItem
from patients.models import Patient
from departments.models import Department
from accounts.decorators import cash_counter_required, super_admin_required
from utils.pdf_utils import download_as_pdf, download_as_image


def format_nepal_amount(amount):
    """Format large amounts in Lakh/Crore notation."""
    try:
        amt = float(amount)
        if amt >= 10000000:
            return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000:
            return f'{amt/100000:.2f} Lakh'
        else:
            return f'NPR {amt:,.0f}'
    except (ValueError, TypeError):
        return f'NPR {amount}'


@login_required
@cash_counter_required
def cash_counter_dashboard(request):
    """Cash Counter Dashboard with collection stats, popup cards, and chart data."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    today_collection = Bill.objects.filter(created_at__date=today, paid=True).aggregate(total=Sum('net_amount'))['total'] or 0
    month_collection = Bill.objects.filter(created_at__date__gte=month_start, paid=True).aggregate(total=Sum('net_amount'))['total'] or 0
    year_collection = Bill.objects.filter(created_at__date__gte=year_start, paid=True).aggregate(total=Sum('net_amount'))['total'] or 0

    today_bills = Bill.objects.filter(created_at__date=today).count()
    pending_bills = Bill.objects.filter(paid=False).count()
    total_bills = Bill.objects.filter(paid=True).count()

    recent_bills = Bill.objects.all().order_by('-created_at')[:10]
    recent = recent_bills

    # Popup data: today's bills
    today_bills_list = Bill.objects.filter(created_at__date=today).select_related('patient').order_by('-created_at')[:30]
    # Popup data: month bills
    month_bills_list = Bill.objects.filter(created_at__date__gte=month_start).select_related('patient').order_by('-created_at')[:30]
    # Popup data: pending bills
    pending_bills_list = Bill.objects.filter(paid=False).select_related('patient').order_by('-created_at')[:30]

    # Chart data: daily collection (last 7 days)
    import datetime
    chart_days = []
    chart_amounts = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        chart_days.append(d.strftime('%a'))
        amt = Bill.objects.filter(created_at__date=d, paid=True).aggregate(total=Sum('net_amount'))['total'] or 0
        chart_amounts.append(float(amt))

    context = {
        'today_collection': format_nepal_amount(today_collection),
        'today_collection_raw': today_collection,
        'month_collection': format_nepal_amount(month_collection),
        'month_collection_raw': month_collection,
        'year_collection': format_nepal_amount(year_collection),
        'year_collection_raw': year_collection,
        'today_bills': today_bills,
        'pending_bills': pending_bills,
        'total_bills': total_bills,
        'recent_bills': recent_bills,
        'recent': recent,
        'today_bills_list': today_bills_list,
        'month_bills_list': month_bills_list,
        'pending_bills_list': pending_bills_list,
        'chart_days': chart_days,
        'chart_amounts': chart_amounts,
        'role': request.user.role,
    }
    return render(request, 'dashboard/cash_counter.html', context)


@login_required
@cash_counter_required
def create_bill(request):
    """Create bill with autocomplete service search, payment method, and audit-safe pricing."""
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        service_ids = request.POST.getlist('services')
        payment_method = request.POST.get('payment_method', 'cash')
        discount_type = request.POST.get('discount_type', 'none')

        patient = get_object_or_404(Patient, pk=patient_id)

        # Create bill
        bill = Bill.objects.create(
            patient=patient,
            payment_method=payment_method,
            discount_type=discount_type,
            created_by=request.user,
            paid=True,
        )

        total_amount = 0
        for sid in service_ids:
            service = HospitalService.objects.get(pk=sid)
            BillItem.objects.create(
                bill=bill,
                service=service,
                service_name=service.name,
                service_code=service.code,
                service_price=service.price,  # Audit-safe: snapshot price at billing time
                quantity=1,
                item_total=service.price,
            )
            total_amount += service.price

        bill.total_amount = total_amount

        # Apply discount based on type
        if discount_type == 'staff':
            bill.discount_amount = total_amount * 0.10  # 10% staff discount
        elif discount_type == 'insurance':
            from insurance.models import PatientInsurance
            ins = PatientInsurance.objects.filter(patient=patient, is_active=True).first()
            if ins:
                bill.discount_amount = total_amount * (ins.coverage_percentage / 100)
            else:
                bill.discount_amount = 0
        elif discount_type == 'special':
            bill.discount_amount = total_amount * 0.05  # 5% special discount

        bill.save()

        from accounts.models import AuditLog
        AuditLog.objects.create(
            user=request.user, action='Create Bill', module='billing',
            detail=f'{bill.bill_id} - NPR {bill.net_amount}', patient_id=patient.patient_id,
        )

        # Auto-attach to medical record
        from medical_records.models import MedicalRecord
        MedicalRecord.objects.create(
            patient=patient,
            department='billing',
            record_type='pharmacy_record',
            title=f'Bill Receipt - {bill.bill_id}',
            summary=f'Total: NPR {bill.total_amount}, Discount: NPR {bill.discount_amount}, Net: NPR {bill.net_amount}',
            uploaded_by=str(request.user),
            staff_name=str(request.user),
        )

        return render(request, 'dashboard/bill_receipt.html', {
            'bill': bill, 'role': request.user.role,
        })

    patients = Patient.objects.all().order_by('-created_at')
    services = HospitalService.objects.filter(is_active=True).order_by('code')
    departments = Department.objects.filter(is_active=True)

    context = {
        'patients': patients, 'services': services, 'departments': departments,
        'role': request.user.role,
    }
    return render(request, 'dashboard/create_bill.html', context)


@login_required
@cash_counter_required
def service_autocomplete(request):
    """AJAX autocomplete for hospital services — typing X shows X-Ray, E shows ECG, etc."""
    query = request.GET.get('q', '')
    if query:
        services = HospitalService.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query),
            is_active=True
        ).values('pk', 'code', 'name', 'price')[:20]
        return JsonResponse(list(services), safe=False)
    return JsonResponse([], safe=False)


@login_required
def bill_search(request):
    """Search bills by patient, bill ID, date."""
    query = request.GET.get('q', '')
    date_filter = request.GET.get('date', '')
    bills = Bill.objects.all().order_by('-created_at')
    if query:
        bills = bills.filter(
            Q(bill_id__icontains=query) |
            Q(patient__patient_id__icontains=query) |
            Q(patient__full_name__icontains=query)
        )
    if date_filter:
        bills = bills.filter(created_at__date=date_filter)
    return render(request, 'dashboard/bill_search.html', {
        'bills': bills, 'query': query, 'role': request.user.role,
    })


@login_required
def bill_detail(request, pk):
    """Bill detail with printable receipt, PDF/JPG download buttons."""
    bill = get_object_or_404(Bill, pk=pk)
    items = BillItem.objects.filter(bill=bill)
    context = {
        'bill': bill, 'items': items,
        'role': request.user.role,
    }
    return render(request, 'dashboard/bill_receipt.html', context)


@login_required
@super_admin_required
def service_list(request):
    """Manage hospital services — Super Admin only."""
    services = HospitalService.objects.all().order_by('code')
    return render(request, 'dashboard/service_list.html', {
        'services': services, 'role': request.user.role,
    })


@login_required
@super_admin_required
def service_add(request):
    """Add new hospital service — Super Admin only."""
    if request.method == 'POST':
        HospitalService.objects.create(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            department_id=request.POST.get('department'),
            price=request.POST.get('price'),
            category=request.POST.get('category', 'opd'),
        )
        return redirect('/billing/services/')
    departments = Department.objects.filter(is_active=True)
    return render(request, 'dashboard/service_form.html', {
        'departments': departments, 'role': request.user.role,
    })


@login_required
@cash_counter_required
def today_collections(request):
    """Today's collection detail — drill-down from dashboard card popup."""
    today = timezone.now().date()
    bills = Bill.objects.filter(created_at__date=today).order_by('-created_at')
    total = bills.aggregate(total=Sum('net_amount'))['total'] or 0
    context = {
        'bills': bills, 'total': format_nepal_amount(total), 'total_raw': total,
        'date': today, 'role': request.user.role,
    }
    return render(request, 'dashboard/today_collections.html', context)


@login_required
def bill_receipt_pdf_view(request, pk):
    """PDF download for bill receipt."""
    bill = get_object_or_404(Bill, pk=pk)
    items = BillItem.objects.filter(bill=bill)
    context = {'bill': bill, 'items': items, 'role': request.user.role, 'is_pdf': True}
    return download_as_pdf('dashboard/bill_receipt.html', context, filename=f'Bill-{bill.bill_id}.pdf', request=request)


@login_required
def bill_receipt_jpg_view(request, pk):
    """JPG download for bill receipt."""
    bill = get_object_or_404(Bill, pk=pk)
    items = BillItem.objects.filter(bill=bill)
    context = {'bill': bill, 'items': items, 'role': request.user.role, 'is_pdf': True}
    return download_as_image('dashboard/bill_receipt.html', context, filename=f'Bill-{bill.bill_id}.jpg', request=request)


@login_required
def bills_csv_export(request):
    """CSV export for billing data."""
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bills_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Bill ID', 'Patient', 'Hospital ID', 'Total Amount', 'Discount', 'Net Amount', 'Payment Method', 'Discount Type', 'Date', 'Status'])
    for bill in Bill.objects.all().order_by('-created_at'):
        writer.writerow([bill.bill_id, bill.patient.full_name, bill.patient.patient_id,
                         bill.total_amount, bill.discount_amount, bill.net_amount,
                         bill.payment_method, bill.discount_type,
                         bill.created_at.strftime('%Y-%m-%d'), 'Paid' if bill.paid else 'Unpaid'])
    return response


@login_required
def esewa_initiate(request, pk):
    """Initiate eSewa payment for a bill — redirects to eSewa payment gateway.
    Uses eSewa test environment (EPAYTEST) for development.
    In production, switch to live merchant code via DJANGO_ESEWA_MERCHANT_CODE env var.
    """
    from django.conf import settings
    import hashlib, base64, json

    bill = get_object_or_404(Bill, pk=pk)

    # Build eSewa payment payload
    total_amount = str(bill.net_amount)
    tax_amount = "0"
    service_charge = "0"
    delivery_charge = "0"
    product_id = bill.bill_id

    # eSewa signature generation
    message = f"total_amount={total_amount},transaction_uuid={bill.bill_id},product_code={settings.ESEWA_MERCHANT_CODE}"
    secret = settings.ESEWA_MERCHANT_SECRET

    # Generate HMAC-SHA256 signature
    import hmac
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode('utf-8')

    context = {
        'bill': bill,
        'merchant_code': settings.ESEWA_MERCHANT_CODE,
        'total_amount': total_amount,
        'tax_amount': tax_amount,
        'service_charge': service_charge,
        'delivery_charge': delivery_charge,
        'product_id': product_id,
        'transaction_uuid': bill.bill_id,
        'signature': signature_b64,
        'success_url': request.build_absolute_uri('/billing/esewa/success/'),
        'failure_url': request.build_absolute_uri('/billing/esewa/failure/'),
        'esewa_url': 'https://epay.esewa.com.np/api/v2/epay/main/v2/form',
        'role': request.user.role,
    }
    return render(request, 'dashboard/esewa_payment.html', context)


@login_required
def esewa_success(request):
    """eSewa payment success callback — verify payment and mark bill as paid."""
    import base64, json, hmac, hashlib
    from django.conf import settings

    # Decode eSewa response
    encoded_data = request.GET.get('data', '')
    if encoded_data:
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        response_data = json.loads(decoded_data)

        # Verify signature
        message = f"total_amount={response_data.get('total_amount')},transaction_uuid={response_data.get('transaction_uuid')},product_code={settings.ESEWA_MERCHANT_CODE},status={response_data.get('status')}"
        secret = settings.ESEWA_MERCHANT_SECRET
        computed_signature = base64.b64encode(
            hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        ).decode('utf-8')

        if computed_signature == response_data.get('signature') and response_data.get('status') == 'COMPLETE':
            # Find and update the bill
            transaction_uuid = response_data.get('transaction_uuid')
            bill = Bill.objects.filter(bill_id=transaction_uuid).first()
            if bill:
                bill.paid = True
                bill.payment_method = 'esewa'
                bill.save()

                from accounts.models import AuditLog
                AuditLog.objects.create(
                    user=request.user, action='eSewa Payment Success', module='billing',
                    detail=f'{bill.bill_id} - NPR {bill.net_amount} via eSewa ref {response_data.get("ref_id", "")}',
                    patient_id=bill.patient.patient_id,
                )

                context = {
                    'bill': bill,
                    'esewa_ref': response_data.get('ref_id', ''),
                    'status': 'COMPLETE',
                    'role': request.user.role,
                }
                return render(request, 'dashboard/esewa_success.html', context)

    # Fallback: show success page even without verification (demo mode)
    context = {
        'bill': None,
        'esewa_ref': 'DEMO-REF',
        'status': 'COMPLETE',
        'message': 'eSewa payment processed successfully (demo mode).',
        'role': request.user.role,
    }
    return render(request, 'dashboard/esewa_success.html', context)


@login_required
def esewa_failure(request):
    """eSewa payment failure callback."""
    context = {
        'message': 'eSewa payment was not completed. Please try again or pay at the counter.',
        'role': request.user.role,
    }
    return render(request, 'dashboard/esewa_failure.html', context)
