from django.db import models
from departments.models import Department
from accounts.models import User


class Doctor(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    qualification = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo = models.ImageField(upload_to='doctors/', blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    schedule = models.TextField(blank=True, help_text='Schedule details e.g. Mon-Fri 9AM-5PM')
    user_account = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'doctor'})
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Dr. {self.name} ({self.department})'

    class Meta:
        ordering = ['name']


WEEKDAY_CHOICES = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
    (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
]


class DoctorQuota(models.Model):
    """OPD Quota system — limits daily patient bookings per doctor per day."""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='quotas')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, help_text='Day of the week')
    max_patients = models.IntegerField(default=50, help_text='Maximum OPD patients for this day')
    start_time = models.TimeField(default='09:00', help_text='OPD start time')
    end_time = models.TimeField(default='14:00', help_text='OPD end time')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['doctor', 'weekday']
        ordering = ['doctor', 'weekday']

    def __str__(self):
        days = dict(WEEKDAY_CHOICES)
        return f'Dr. {self.doctor.name} - {days[self.weekday]} - Max {self.max_patients} patients'

    @property
    def booked_today(self):
        """Count booked visits for this doctor on this weekday."""
        from patients.models import OPDVisit
        from django.utils import timezone
        today = timezone.now().date()
        return OPDVisit.objects.filter(
            doctor=self.doctor, visit_date__date=today
        ).count()

    @property
    def available_slots(self):
        """Remaining slots available for booking."""
        return max(0, self.max_patients - self.booked_today)

    @property
    def is_quota_full(self):
        """Whether quota is fully booked."""
        return self.available_slots <= 0
