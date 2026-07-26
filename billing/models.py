from django.db import models
from django.conf import settings
from patients.models import Patient, PAYMENT_METHOD_CHOICES
from departments.models import Department
from accounts.models import User
from utils.barcode_utils import generate_barcode_for_object


class HospitalService(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=[
        ('opd', 'OPD'), ('laboratory', 'Laboratory'), ('radiology', 'Radiology'),
        ('ecg', 'ECG'), ('ultrasound', 'Ultrasound'), ('xray', 'X-Ray'),
        ('pharmacy', 'Pharmacy'), ('procedure', 'Procedure'), ('other', 'Other'),
    ], default='opd')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.code} - {self.name} (NPR {self.price})'

    class Meta:
        ordering = ['code']


def generate_bill_id():
    prefix = 'BIL-'
    last = Bill.objects.filter(bill_id__startswith=prefix).order_by('-bill_id').first()
    if last:
        try:
            num = int(last.bill_id.replace(prefix, '')) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f'{prefix}{num:06d}'


class Bill(models.Model):
    bill_id = models.CharField(max_length=20, unique=True, default=generate_bill_id, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    services = models.ManyToManyField(HospitalService, through='BillItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    discount_type = models.CharField(max_length=30, choices=[
        ('none', 'No Discount'), ('staff', 'Staff Discount'), ('insurance', 'Insurance Discount'),
        ('special', 'Special Discount')], default='none')
    paid = models.BooleanField(default=True)
    barcode = models.ImageField(upload_to='barcodes/', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bills')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate net amount
        self.net_amount = self.total_amount - self.discount_amount
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # Generate barcode on first save
        if is_new and not self.barcode:
            generate_barcode_for_object(self, 'barcode')

    @property
    def amount_display(self):
        """Format amount in lakh/crore notation."""
        return settings.format_npr(self.net_amount) if hasattr(settings, 'format_npr') else f'NPR {self.net_amount}'

    def __str__(self):
        return f'{self.bill_id} - {self.patient.full_name}'

    class Meta:
        ordering = ['-created_at']


class BillItem(models.Model):
    """Audit-safe snapshot: stores service price at time of billing to prevent retroactive changes."""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='bill_items')
    service = models.ForeignKey(HospitalService, on_delete=models.SET_NULL, null=True)
    # Snapshot fields — frozen at time of billing
    service_name = models.CharField(max_length=200)
    service_code = models.CharField(max_length=50)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.service and not self.service_name:
            self.service_name = self.service.name
            self.service_code = self.service.code
            self.service_price = self.service.price
        self.item_total = self.service_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.service_name} x {self.quantity} = NPR {self.item_total}'
