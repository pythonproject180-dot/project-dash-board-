from django.db import models
from patients.models import Patient, OPDVisit
from doctors.models import Doctor

class Prescription(models.Model):
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True)

class Consultation(models.Model):
    visit = models.ForeignKey(OPDVisit, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    diagnosis = models.TextField(blank=True)
    clinical_notes = models.TextField(blank=True)
    prescriptions = models.ManyToManyField(Prescription, blank=True)
    follow_up_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation - {self.visit.patient.full_name}"

class LabTestRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    test_name = models.CharField(max_length=200)
    clinical_note = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')], default='routine')
    status = models.CharField(max_length=20, choices=[
        ('pending','Pending'),('accepted','Accepted'),('sample_collected','Sample Collected'),
        ('testing','Testing'),('completed','Completed')], default='pending')
    result_notes = models.TextField(blank=True)
    result_file = models.FileField(upload_to='lab_results/', blank=True)
    referral_file = models.FileField(upload_to='lab_referrals/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    barcode = models.ImageField(upload_to='barcodes/lab/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            code_str = f'LAB-{self.pk}'
            content, filename = generate_barcode(code_str, save_path_prefix='barcodes/lab/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def __str__(self):
        return f"Lab-{self.patient.patient_id} - {self.test_name}"

class RadiologyRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    imaging_type = models.CharField(max_length=50, choices=[
        ('xray','X-Ray'),('ct','CT'),('mri','MRI'),('ecg','ECG'),('echo','Echo'),('ultrasound','Ultrasound'),('custom','Custom')])
    custom_type = models.CharField(max_length=200, blank=True)
    clinical_note = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')], default='routine')
    status = models.CharField(max_length=20, choices=[
        ('requested','Requested'),('scheduled','Scheduled'),('in_progress','In Progress'),('completed','Completed')], default='requested')
    findings = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    result_notes = models.TextField(blank=True)
    result_file = models.FileField(upload_to='radiology_results/', blank=True)
    referral_file = models.FileField(upload_to='radiology_referrals/', blank=True)
    request_id = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    barcode = models.ImageField(upload_to='barcodes/radiology/', blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.request_id:
            year = '2026'
            last = RadiologyRequest.objects.filter(request_id__startswith=f'RAD-{year}-').order_by('-request_id').first()
            if last:
                num = int(last.request_id.split('-')[-1]) + 1
            else:
                num = 1
            self.request_id = f'RAD-{year}-{num:06d}'
        super().save(*args, **kwargs)
        if is_new and not self.barcode:
            from utils.barcode_utils import generate_barcode
            content, filename = generate_barcode(self.request_id, save_path_prefix='barcodes/radiology/')
            self.barcode.save(filename, content)
            super().save(update_fields=['barcode'])

    def __str__(self):
        return f"{self.request_id} - {self.patient.full_name}"
