from django.db import models
from django.utils import timezone
from patients.models import Patient
from doctors.models import Doctor
from departments.models import Department
from accounts.models import Province, District


class Ward(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    floor = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Bed(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    bed_number = models.CharField(max_length=20)
    is_occupied = models.BooleanField(default=False)
    bed_type = models.CharField(max_length=50, choices=[
        ('general', 'General'), ('semi_private', 'Semi-Private'),
        ('private', 'Private'), ('icu', 'ICU'), ('nicu', 'NICU')], default='general')

    def __str__(self):
        return f'{self.ward.name} - Bed {self.bed_number}'


def generate_admission_id():
    prefix = 'ADM-'
    last = Admission.objects.filter(admission_id__startswith=prefix).order_by('-admission_id').first()
    if last:
        try:
            num = int(last.admission_id.replace(prefix, '')) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f'{prefix}{num:06d}'


class Admission(models.Model):
    admission_id = models.CharField(max_length=20, unique=True, default=generate_admission_id, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True)
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True)
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(blank=True, null=True)
    diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('admitted', 'Admitted'), ('discharged', 'Discharged')], default='admitted')
    admission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    barcode = models.ImageField(upload_to='barcodes/admissions/', blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            content, filename = generate_barcode(self.admission_id, save_path_prefix='barcodes/admissions/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def discharge(self):
        self.status = 'discharged'
        self.discharge_date = timezone.now()
        if self.bed:
            self.bed.is_occupied = False
            self.bed.save()
        self.save()

    def __str__(self):
        return f'{self.admission_id} - {self.patient.full_name}'


class DischargeSummary(models.Model):
    """Formal A4-printable discharge summary document."""
    admission = models.OneToOneField(Admission, on_delete=models.CASCADE, related_name='discharge_summary')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    attending_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    # Clinical details
    admission_diagnosis = models.TextField(blank=True)
    final_diagnosis = models.TextField(blank=True)
    chief_complaint = models.TextField(blank=True)
    history_of_present_illness = models.TextField(blank=True)
    examination_findings = models.TextField(blank=True)
    investigations = models.TextField(blank=True, help_text='Lab/Radiology findings summary')
    treatment_given = models.TextField(blank=True)
    condition_at_discharge = models.CharField(max_length=50, choices=[
        ('improved', 'Improved'), ('stable', 'Stable'),
        ('unchanged', 'Unchanged'), ('deteriorated', 'Deteriorated')], default='improved')
    discharge_instructions = models.TextField(blank=True, help_text='Instructions for patient after discharge')
    follow_up_date = models.DateField(blank=True, null=True)
    follow_up_instructions = models.TextField(blank=True)
    medications_at_discharge = models.TextField(blank=True, help_text='List of medications prescribed at discharge')
    # Metadata
    prepared_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    prepared_at = models.DateTimeField(auto_now_add=True)
    approved_by_doctor = models.BooleanField(default=False)
    barcode = models.ImageField(upload_to='barcodes/discharge/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            content, filename = generate_barcode(f'DSUM-{self.pk}', save_path_prefix='barcodes/discharge/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def __str__(self):
        return f'Discharge Summary - {self.patient.full_name}'
