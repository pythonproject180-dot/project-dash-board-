from django.db import models
from django.contrib.auth.models import AbstractUser

ROLE_CHOICES = [
    ('super_admin', 'Super Admin'),
    ('registration', 'Registration Counter'),
    ('cash_counter', 'Cash Counter'),
    ('doctor', 'Doctor'),
    ('pharmacy', 'Pharmacy'),
    ('laboratory', 'Laboratory'),
    ('radiology', 'Radiology Counter'),
    ('insurance', 'Insurance Counter'),
    ('admission', 'Ward/Admission'),
    ('nursing', 'Nursing'),
    ('operation_theatre', 'Operation Theatre'),
    ('blood_bank', 'Blood Bank'),
    ('accounts', 'Accounts Department'),
    ('medical_records', 'Medical Records'),
]

class User(AbstractUser):
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='registration')
    phone = models.CharField(max_length=20, blank=True)
    is_active_staff = models.BooleanField(default=True)

    DASHBOARD_URLS = {
        'super_admin': '/accounts/dashboard/super-admin/',
        'registration': '/patients/dashboard/',
        'cash_counter': '/billing/',
        'doctor': '/doctors/dashboard/',
        'pharmacy': '/pharmacy/',
        'laboratory': '/laboratory/',
        'radiology': '/radiology/',
        'insurance': '/insurance/',
        'admission': '/admissions/',
        'nursing': '/nursing/',
        'operation_theatre': '/operation-theatre/',
        'blood_bank': '/blood-bank/',
        'accounts': '/reports/accounts/',
        'medical_records': '/medical-records/',
    }

    def get_dashboard_url(self):
        if self.is_superuser:
            return self.DASHBOARD_URLS.get('super_admin')
        return self.DASHBOARD_URLS.get(self.role, '/accounts/login/')

    @property
    def role_display(self):
        return dict(ROLE_CHOICES).get(self.role, self.role)

    class Meta:
        verbose_name = 'Staff User'
        verbose_name_plural = 'Staff Users'


class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    module = models.CharField(max_length=50)
    detail = models.TextField(blank=True)
    patient_id = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['-timestamp']


class Province(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.province.name})"
