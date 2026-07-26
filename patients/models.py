import qrcode
import io
from django.db import models
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from departments.models import Department
from doctors.models import Doctor
from accounts.models import Province, District

AGE_TYPE_CHOICES = [
    ('years', 'Years'),
    ('months', 'Months'),
    ('weeks', 'Weeks'),
    ('days', 'Days'),
]

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('esewa', 'eSewa'),
]

def generate_patient_id():
    """Generate sequential Hospital ID — shared sequence for online and counter registration."""
    prefix = 'HT-'
    last = Patient.objects.filter(patient_id__startswith=prefix).order_by('-patient_id').first()
    if last:
        try:
            num = int(last.patient_id.replace(prefix, '')) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f'{prefix}{num:06d}'


class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, default=generate_patient_id, editable=False)
    # Name fields — split for proper form handling
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, editable=False)  # Auto-computed
    # Age fields — support years/months/weeks/days
    age_value = models.IntegerField(default=0, help_text='Age numeric value')
    age_type = models.CharField(max_length=10, choices=AGE_TYPE_CHOICES, default='years')
    date_of_birth = models.DateField(null=True, blank=True, help_text='Optional — if provided, age is auto-calculated')
    gender = models.CharField(max_length=10, choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    phone = models.CharField(max_length=20, unique=True, help_text='Primary phone number')
    email = models.EmailField(blank=True)
    # Nepal address fields
    address_line = models.TextField(blank=True)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.CharField(max_length=200, blank=True, help_text='Municipality/Rural Municipality')
    ward_number = models.CharField(max_length=20, blank=True, help_text='Ward Number')
    tole = models.CharField(max_length=200, blank=True, help_text='Tole/Street name')
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, help_text='Emergency contact person name')
    emergency_contact_phone = models.CharField(max_length=20, blank=True, help_text='Emergency contact phone')
    emergency_contact_relation = models.CharField(max_length=100, blank=True, help_text='Relation to patient')
    # Medical info
    blood_group = models.CharField(max_length=10, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ])
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    # Media
    photo = models.ImageField(upload_to='patients/', blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)
    # Registration metadata
    registered_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='registered_patients')
    registration_source = models.CharField(max_length=20, choices=[
        ('counter', 'Registration Counter'), ('online', 'Online Portal')], default='counter')
    is_new_patient = models.BooleanField(default=True, help_text='New vs returning patient for fee calculation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-compute full_name
        self.full_name = f'{self.first_name} {self.last_name}'.strip()
        # Determine if new or returning patient
        if self.pk:
            existing_visits = OPDVisit.objects.filter(patient=self).count()
            self.is_new_patient = existing_visits <= 0
        super().save(*args, **kwargs)
        # Generate QR code on first save
        if not self.qr_code:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f'hamro-hospital://patient/{self.patient_id}')
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            filename = f'qr_{self.patient_id}.png'
            self.qr_code.save(filename, ContentFile(buf.getvalue()))

    @property
    def age_display(self):
        """Return age in display format: '24 Years', '3 Months', etc."""
        return f'{self.age_value} {dict(AGE_TYPE_CHOICES).get(self.age_type, self.age_type)}'

    @property
    def registration_fee(self):
        """Return appropriate registration fee based on new/returning status."""
        return settings.REGISTRATION_FEE_NEW if self.is_new_patient else settings.REGISTRATION_FEE_OLD

    @property
    def address_display(self):
        """Return formatted Nepal address."""
        parts = [self.tole, self.ward_number, self.municipality]
        if self.district:
            parts.append(str(self.district))
        if self.province:
            parts.append(str(self.province))
        return ', '.join(filter(None, parts)) or self.address_line

    def __str__(self):
        return f'{self.patient_id} - {self.full_name}'

    class Meta:
        ordering = ['-created_at']


class OPDVisit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='opd_visits')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    token_number = models.IntegerField(default=1)
    visit_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('waiting', 'Waiting'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='waiting')
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    visit_type = models.CharField(max_length=20, choices=[
        ('new', 'New Patient'), ('follow_up', 'Follow-up')], default='new')
    clinical_notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f'Visit {self.token_number} - {self.patient.full_name}'
