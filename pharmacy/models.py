from django.db import models
from departments.models import Department

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=50, unique=True)
    manufacturer = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=50, default='Tablet')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=10)
    expiry_date = models.DateField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return 'out_of_stock'
        elif self.stock_quantity <= self.minimum_stock:
            return 'low_stock'
        return 'in_stock'

    def __str__(self):
        return f"{self.code} - {self.name}"

def generate_sale_id():
    year = '2026'
    last = PharmacySale.objects.filter(sale_id__startswith=f'PHR-{year}-').order_by('-sale_id').first()
    if last:
        num = int(last.sale_id.split('-')[-1]) + 1
    else:
        num = 1
    return f'PHR-{year}-{num:06d}'

class PharmacySale(models.Model):
    sale_id = models.CharField(max_length=20, unique=True, default=generate_sale_id)
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    items = models.ManyToManyField(Medicine, through='SaleItem')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash','Cash'),('esewa','eSewa'),('card','Card'),('insurance','Insurance')], default='cash')
    counter_staff = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    prescription_ref = models.CharField(max_length=200, blank=True)
    barcode = models.ImageField(upload_to='barcodes/pharmacy/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            content, filename = generate_barcode(self.sale_id, save_path_prefix='barcodes/pharmacy/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def __str__(self):
        return f"{self.sale_id}"

class SaleItem(models.Model):
    sale = models.ForeignKey(PharmacySale, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
