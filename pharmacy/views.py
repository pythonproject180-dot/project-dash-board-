from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, F, Sum, Count
from .models import Medicine, PharmacySale, SaleItem
from patients.models import Patient
from accounts.decorators import pharmacy_required, super_admin_required
from accounts.models import AuditLog
from medical_records.models import MedicalRecord


def fmt(amount):
    try:
        amt = float(amount)
        if amt >= 10000000: return f'{amt/10000000:.2f} Crore'
        elif amt >= 100000: return f'{amt/100000:.2f} Lakh'
        else: return f'NPR {amt:,.0f}'
    except: return f'NPR {amount}'


@login_required
@pharmacy_required
def pharmacy_dashboard(request):
    """Pharmacy Dashboard with sales stats."""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    today_sales = PharmacySale.objects.filter(sale_date__date=today).aggregate(total=Sum('final_amount'))['total'] or 0
    month_sales = PharmacySale.objects.filter(sale_date__date__gte=month_start).aggregate(total=Sum('final_amount'))['total'] or 0
    year_sales = PharmacySale.objects.filter(sale_date__date__gte=year_start).aggregate(total=Sum('final_amount'))['total'] or 0

    total_medicines = Medicine.objects.filter(is_active=True).count()
    low_stock = Medicine.objects.filter(stock_quantity__lte=F('minimum_stock')).count()
    out_of_stock = Medicine.objects.filter(stock_quantity__lte=0).count()

    recent_sales = PharmacySale.objects.all().order_by('-sale_date')[:10]

    context = {
        'today_sales': fmt(today_sales), 'today_sales_raw': today_sales,
        'month_sales': fmt(month_sales), 'month_sales_raw': month_sales,
        'year_sales': fmt(year_sales), 'year_sales_raw': year_sales,
        'total_medicines': total_medicines,
        'low_stock': low_stock, 'out_of_stock': out_of_stock,
        'recent_sales': recent_sales,
        'role': request.user.role,
    }
    return render(request, 'dashboard/pharmacy.html', context)


@login_required
def medicine_list(request):
    """Medicine list with search and stock status."""
    query = request.GET.get('q', '')
    medicines = Medicine.objects.filter(is_active=True).order_by('code')
    if query:
        medicines = medicines.filter(
            Q(code__icontains=query) | Q(name__icontains=query) | Q(generic_name__icontains=query)
        )
    context = {'medicines': medicines, 'query': query, 'role': request.user.role}
    return render(request, 'dashboard/medicine_list.html', context)


@login_required
@super_admin_required
def medicine_add(request):
    """Add medicine — Super Admin only."""
    if request.method == 'POST':
        Medicine.objects.create(
            name=request.POST.get('name'),
            generic_name=request.POST.get('generic_name', ''),
            code=request.POST.get('code'),
            manufacturer=request.POST.get('manufacturer', ''),
            unit=request.POST.get('unit', 'Tablet'),
            price=request.POST.get('price', 0),
            stock_quantity=request.POST.get('stock_quantity', 0),
            minimum_stock=request.POST.get('minimum_stock', 10),
            expiry_date=request.POST.get('expiry_date') or None,
        )
        return redirect('/pharmacy/medicines/')
    return render(request, 'dashboard/medicine_form.html', {'role': 'super_admin'})


@login_required
@pharmacy_required
def pharmacy_dispense(request):
    """Dispense medicine to patient."""
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        payment_method = request.POST.get('payment_method', 'cash')

        patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None

        sale = PharmacySale.objects.create(
            patient=patient,
            payment_method=payment_method,
            counter_staff=request.user,
            prescription_ref=request.POST.get('prescription_ref', ''),
        )

        total_amount = 0
        med_ids = request.POST.getlist('medicines')
        quantities = request.POST.getlist('quantities')
        for i, med_id in enumerate(med_ids):
            medicine = Medicine.objects.get(pk=med_id)
            qty = int(quantities[i]) if i < len(quantities) else 1
            item_total = medicine.price * qty
            SaleItem.objects.create(
                sale=sale, medicine=medicine,
                quantity=qty, price_at_sale=medicine.price,
                total=item_total,
            )
            total_amount += item_total
            # Update stock
            medicine.stock_quantity = F('stock_quantity') - qty
            medicine.save()

        sale.total_amount = total_amount
        sale.final_amount = total_amount - sale.discount
        sale.save()

        # Auto-attach to medical record
        if patient:
            MedicalRecord.objects.create(
                patient=patient, department='pharmacy',
                record_type='pharmacy_record',
                title=f'Pharmacy Sale - {sale.sale_id}',
                summary=f'Total: NPR {sale.final_amount}',
                uploaded_by=str(request.user), staff_name=str(request.user),
            )

        AuditLog.objects.create(
            user=request.user, action='Pharmacy Sale', module='pharmacy',
            detail=f'{sale.sale_id} - NPR {sale.final_amount}',
        )

        return render(request, 'dashboard/pharmacy_bill.html', {
            'sale': sale, 'role': request.user.role,
        })

    patients = Patient.objects.all().order_by('-created_at')
    medicines = Medicine.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
    return render(request, 'dashboard/dispense.html', {
        'patients': patients, 'medicines': medicines, 'role': request.user.role,
    })


@login_required
def pharmacy_report(request):
    """Pharmacy sales report — filter by date, patient, medicine."""
    from django.db.models import F
    today = timezone.now().date()
    month_start = today.replace(day=1)

    date_filter = request.GET.get('date', '')
    patient_filter = request.GET.get('patient', '')

    sales = PharmacySale.objects.all().order_by('-sale_date')
    if date_filter:
        sales = sales.filter(sale_date__date=date_filter)
    if patient_filter:
        sales = sales.filter(patient_id=patient_filter)

    total = sales.aggregate(total=Sum('final_amount'))['total'] or 0

    context = {
        'sales': sales, 'total': fmt(total), 'total_raw': total,
        'date_filter': date_filter, 'patient_filter': patient_filter,
        'role': request.user.role,
    }
    return render(request, 'dashboard/pharmacy_report.html', context)
