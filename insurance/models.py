from django.db import models
from patients.models import Patient

class Insurer(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class PatientInsurance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    insurer = models.ForeignKey(Insurer, on_delete=models.SET_NULL, null=True)
    policy_number = models.CharField(max_length=100)
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.insurer}"

def generate_claim_id():
    year = '2026'
    last = InsuranceClaim.objects.filter(claim_id__startswith=f'CLM-{year}-').order_by('-claim_id').first()
    if last:
        num = int(last.claim_id.split('-')[-1]) + 1
    else:
        num = 1
    return f'CLM-{year}-{num:06d}'

class InsuranceClaim(models.Model):
    claim_id = models.CharField(max_length=20, unique=True, default=generate_claim_id)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    insurance = models.ForeignKey(PatientInsurance, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'),('approved','Approved'),('rejected','Rejected'),('settled','Settled')], default='pending')
    supporting_documents = models.FileField(upload_to='insurance_docs/', blank=True)
    notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    barcode = models.ImageField(upload_to='barcodes/insurance/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            content, filename = generate_barcode(self.claim_id, save_path_prefix='barcodes/insurance/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def __str__(self):
        return f"{self.claim_id} - {self.patient.full_name}"
