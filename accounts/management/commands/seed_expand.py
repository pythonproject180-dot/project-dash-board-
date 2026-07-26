from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User, Province, District
from departments.models import Department
from doctors.models import Doctor, DoctorQuota, WEEKDAY_CHOICES
from patients.models import Patient, OPDVisit
from billing.models import HospitalService, Bill, BillItem
from consultations.models import Consultation, Prescription, LabTestRequest, RadiologyRequest
from laboratory.models import LabCatalog
from radiology.models import RadiologyCatalog
from pharmacy.models import Medicine, PharmacySale, SaleItem
from admissions.models import Ward, Bed, Admission, DischargeSummary
from insurance.models import Insurer, PatientInsurance, InsuranceClaim
from medical_records.models import MedicalRecord
from appointments.models import Appointment
from nursing.models import NursingNote
from operation_theatre.models import Surgery
from blood_bank.models import BloodRequest
from website.models import GalleryImage, Testimonial, DiseaseInfo
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta, date, time


class Command(BaseCommand):
    help = 'Expand seed data: 100 medicines, 10+ items per category, eSewa payments, appointments, surgeries, nursing notes, blood requests, discharge summaries'

    def handle(self, *args, **options):
        self.stdout.write('=== EXPANDING SEED DATA ===\n')

        # ===== 1. EXPAND MEDICINES TO 100 =====
        self.stdout.write('Adding 90 more medicines (total target: 100)...\n')
        medicine_data = [
            ('MED-011', 'Paracetamol 650mg', 'Paracetamol', 'Acme Pharma', 'Tablet', 15, 500),
            ('MED-012', 'Ibuprofen 400mg', 'Ibuprofen', 'Nepal Pharma', 'Tablet', 25, 300),
            ('MED-013', 'Amoxicillin 500mg', 'Amoxicillin', 'Asian Medicines', 'Capsule', 35, 200),
            ('MED-014', 'Ciprofloxacin 500mg', 'Ciprofloxacin', 'Zenith Labs', 'Tablet', 40, 150),
            ('MED-015', 'Metformin 500mg', 'Metformin', 'Glenmark', 'Tablet', 20, 800),
            ('MED-016', 'Atenolol 50mg', 'Atenolol', 'Cipla Nepal', 'Tablet', 30, 400),
            ('MED-017', 'Omeprazole 20mg', 'Omeprazole', 'Dawn Pharma', 'Capsule', 45, 350),
            ('MED-018', 'Amlodipine 5mg', 'Amlodipine', 'Micro Labs', 'Tablet', 28, 600),
            ('MED-019', 'Azithromycin 500mg', 'Azithromycin', 'Alembic Pharma', 'Tablet', 55, 100),
            ('MED-020', 'Cetirizine 10mg', 'Cetirizine', 'Dr Reddy', 'Tablet', 12, 700),
            ('MED-021', 'Doxycycline 100mg', 'Doxycycline', 'Mankind', 'Capsule', 38, 180),
            ('MED-022', 'Fluoxetine 20mg', 'Fluoxetine', 'Sun Pharma', 'Capsule', 42, 250),
            ('MED-023', 'Losartan 50mg', 'Losartan', 'Torrent Pharma', 'Tablet', 32, 500),
            ('MED-024', 'Montelukast 10mg', 'Montelukast', 'Lupin Nepal', 'Tablet', 35, 400),
            ('MED-025', 'Pantoprazole 40mg', 'Pantoprazole', 'Alkem Labs', 'Tablet', 48, 300),
            ('MED-026', 'Ranitidine 150mg', 'Ranitidine', 'Jubilant', 'Tablet', 18, 600),
            ('MED-027', 'Salbutamol 2mg', 'Salbutamol', 'Cipla', 'Tablet', 22, 500),
            ('MED-028', 'Simvastatin 20mg', 'Simvastatin', 'Zydus Cadila', 'Tablet', 30, 350),
            ('MED-029', 'Tramadol 50mg', 'Tramadol', 'Abbott Nepal', 'Tablet', 65, 80),
            ('MED-030', 'Warfarin 5mg', 'Warfarin', 'Bristol-Myers', 'Tablet', 80, 50),
            ('MED-031', 'Aspirin 300mg', 'Aspirin', 'USV Pvt Ltd', 'Tablet', 8, 900),
            ('MED-032', 'Diazepam 5mg', 'Diazepam', 'RPG Life', 'Tablet', 55, 40),
            ('MED-033', 'Furosemide 40mg', 'Furosemide', 'Intas Pharma', 'Tablet', 25, 300),
            ('MED-034', 'Hydrochlorothiazide 25mg', 'HCTZ', 'Novartis Nepal', 'Tablet', 20, 500),
            ('MED-035', 'Levothyroxine 50mcg', 'Levothyroxine', 'Merck Nepal', 'Tablet', 40, 250),
            ('MED-036', 'Naproxen 250mg', 'Naproxen', 'Syntec Pharma', 'Tablet', 30, 200),
            ('MED-037', 'Nifedipine 10mg', 'Nifedipine', 'Bayer Nepal', 'Capsule', 35, 150),
            ('MED-038', 'Prednisolone 5mg', 'Prednisolone', 'Wyeth Nepal', 'Tablet', 22, 400),
            ('MED-039', 'Spironolactone 25mg', 'Spironolactone', 'Ranbaxy', 'Tablet', 28, 300),
            ('MED-040', 'Tamsulosin 0.4mg', 'Tamsulosin', 'Boehringer', 'Capsule', 50, 200),
            ('MED-041', 'Digoxin 0.25mg', 'Digoxin', 'GSK Nepal', 'Tablet', 75, 30),
            ('MED-042', 'Enalapril 5mg', 'Enalapril', ' MSD Nepal', 'Tablet', 32, 400),
            ('MED-043', 'Glimepiride 2mg', 'Glimepiride', 'Aventis Nepal', 'Tablet', 38, 300),
            ('MED-044', 'Insulin Glargine', 'Insulin Glargine', 'Sanofi', 'Injection', 850, 20),
            ('MED-045', 'Calcium+Vitamin D3', 'Calcium Carbonate+VitD3', 'Abbott', 'Tablet', 55, 400),
            ('MED-046', 'Iron+Folic Acid', 'Ferrous Sulphate+Folic Acid', 'Emcure', 'Tablet', 30, 500),
            ('MED-047', 'ORS Powder', 'Oral Rehydration Salts', 'UNICEF Nepal', 'Powder', 25, 800),
            ('MED-048', 'Loperamide 2mg', 'Loperamide', 'Janssen Nepal', 'Capsule', 18, 600),
            ('MED-049', 'Phenobarbitone 30mg', 'Phenobarbitone', 'Abbott', 'Tablet', 40, 50),
            ('MED-050', 'Carbamazepine 200mg', 'Carbamazepine', 'Novartis', 'Tablet', 35, 200),
            ('MED-051', 'Valproate 200mg', 'Valproic Acid', 'Sanofi Nepal', 'Tablet', 45, 150),
            ('MED-052', 'Albendazole 400mg', 'Albendazole', 'GSK', 'Tablet', 10, 800),
            ('MED-053', 'Mebendazole 100mg', 'Mebendazole', 'Janssen', 'Tablet', 12, 700),
            ('MED-054', 'Ivermectin 6mg', 'Ivermectin', 'MSD Nepal', 'Tablet', 30, 400),
            ('MED-055', 'Praziquantel 600mg', 'Praziquantel', 'Merck', 'Tablet', 40, 300),
            ('MED-056', 'Chloroquine 250mg', 'Chloroquine', 'IPCA Labs', 'Tablet', 20, 500),
            ('MED-057', 'Artemether+Lumefantrine', 'Coartem', 'Novartis', 'Tablet', 120, 200),
            ('MED-058', 'Dapsone 100mg', 'Dapsone', 'GSK Nepal', 'Tablet', 25, 300),
            ('MED-059', 'Clofazimine 50mg', 'Clofazimine', 'Novartis', 'Capsule', 30, 200),
            ('MED-060', 'Rifampicin 150mg', 'Rifampicin', 'Lupin', 'Capsule', 15, 400),
            ('MED-061', 'Isoniazid 100mg', 'Isoniazid', 'Cipla Nepal', 'Tablet', 8, 600),
            ('MED-062', 'Ethambutol 400mg', 'Ethambutol', 'Macleods', 'Tablet', 12, 500),
            ('MED-063', 'Pyrazinamide 500mg', 'Pyrazinamide', 'Lupin', 'Tablet', 18, 400),
            ('MED-064', 'Streptomycin 1g', 'Streptomycin', 'Macleods', 'Injection', 45, 150),
            ('MED-065', 'Cephalexin 500mg', 'Cephalexin', 'Glenmark Nepal', 'Capsule', 32, 300),
            ('MED-066', 'Gentamicin 80mg', 'Gentamicin', 'Intas Nepal', 'Injection', 40, 200),
            ('MED-067', 'Vancomycin 500mg', 'Vancomycin', 'Mylan Nepal', 'Injection', 350, 30),
            ('MED-068', 'Meropenem 1g', 'Meropenem', 'AstraZeneca', 'Injection', 500, 20),
            ('MED-069', 'Clindamycin 300mg', 'Clindamycin', 'Pfizer Nepal', 'Capsule', 38, 250),
            ('MED-070', 'Erythromycin 250mg', 'Erythromycin', 'Abbott', 'Tablet', 25, 300),
            ('MED-071', 'Nitrofurantoin 100mg', 'Nitrofurantoin', 'IPCA Nepal', 'Capsule', 28, 250),
            ('MED-072', 'Norfloxacin 400mg', 'Norfloxacin', 'Ranbaxy', 'Tablet', 30, 200),
            ('MED-073', 'Trimethoprim+Sulfamethoxazole', 'Co-trimoxazole', 'GSK Nepal', 'Tablet', 15, 500),
            ('MED-074', 'Metronidazole 400mg', 'Metronidazole', 'IPCA Labs', 'Tablet', 20, 400),
            ('MED-075', 'Fluconazole 150mg', 'Fluconazole', 'Pfizer Nepal', 'Capsule', 50, 200),
            ('MED-076', 'Acyclovir 200mg', 'Acyclovir', 'GSK Nepal', 'Tablet', 35, 300),
            ('MED-077', 'Ganciclovir 500mg', 'Ganciclovir', 'Roche Nepal', 'Capsule', 200, 40),
            ('MED-078', 'Zidovudine 300mg', 'Zidovudine', 'GSK', 'Capsule', 80, 100),
            ('MED-079', 'Lamivudine 150mg', 'Lamivudine', 'GSK Nepal', 'Tablet', 60, 150),
            ('MED-080', 'Tenofovir 300mg', 'Tenofovir', 'Gilead Nepal', 'Tablet', 70, 200),
            ('MED-081', 'Heparin 5000IU', 'Heparin', 'Sun Pharma', 'Injection', 120, 50),
            ('MED-082', 'Enoxaparin 40mg', 'Enoxaparin', 'Sanofi Nepal', 'Injection', 450, 20),
            ('MED-083', 'Adrenaline 1mg', 'Epinephrine', 'Pfizer Nepal', 'Injection', 30, 100),
            ('MED-084', 'Atropine 0.6mg', 'Atropine', 'RPG Nepal', 'Injection', 25, 80),
            ('MED-085', 'Dopamine 200mg', 'Dopamine', 'Sun Pharma', 'Injection', 150, 40),
            ('MED-086', 'Naloxone 0.4mg', 'Naloxone', 'Teva Nepal', 'Injection', 200, 30),
            ('MED-087', 'Midazolam 5mg', 'Midazolam', 'Ranbaxy Nepal', 'Injection', 50, 80),
            ('MED-088', 'Morphine 10mg', 'Morphine', 'GSK Nepal', 'Injection', 80, 50),
            ('MED-089', 'Propofol 200mg', 'Propofol', 'Fresenius Nepal', 'Injection', 300, 30),
            ('MED-090', 'Succinylcholine 100mg', 'Suxamethonium', 'Sun Pharma', 'Injection', 60, 50),
            ('MED-091', 'Vecuronium 4mg', 'Vecuronium', 'Organon Nepal', 'Injection', 250, 30),
            ('MED-092', 'Neostigmine 2.5mg', 'Neostigmine', 'RPG Labs', 'Injection', 40, 60),
            ('MED-093', 'Lactulose 10g/15ml', 'Lactulose', 'Abbott Nepal', 'Syrup', 120, 200),
            ('MED-094', 'Polyethylene Glycol', 'PEG 3350', 'Braintree Labs', 'Powder', 150, 150),
            ('MED-095', 'Sucralfate 1g', 'Sucralfate', 'Quad Nepal', 'Tablet', 35, 300),
            ('MED-096', 'Bisacodyl 5mg', 'Bisacodyl', 'Emcure Nepal', 'Tablet', 10, 600),
            ('MED-097', 'Senna Leaves Extract', 'Sennosides', 'Herb Nepal', 'Tablet', 8, 500),
            ('MED-098', 'Vitamin B Complex', 'Thiamine+Riboflavin+Niacin', 'USV Nepal', 'Tablet', 25, 400),
            ('MED-099', 'Vitamin C 500mg', 'Ascorbic Acid', 'Abbott Nepal', 'Tablet', 15, 600),
            ('MED-100', 'Multivitamin+Mineral', 'Multivitamin', 'Centrum Nepal', 'Tablet', 60, 300),
        ]

        dept_map = {d.name: d for d in Department.objects.all()}
        pharmacy_dept = dept_map.get('Pharmacy')

        for code, name, generic, manufacturer, unit, price, stock in medicine_data:
            if not Medicine.objects.filter(code=code).exists():
                Medicine.objects.create(
                    code=code, name=name, generic_name=generic,
                    manufacturer=manufacturer, unit=unit,
                    price=Decimal(str(price)), stock_quantity=stock,
                    minimum_stock=max(10, stock//5), department=pharmacy_dept,
                    is_active=True,
                )
        self.stdout.write(f'  Medicines total: {Medicine.objects.count()}\n')

        # ===== 2. EXPAND HOSPITAL SERVICES =====
        self.stdout.write('Adding more hospital services...\n')
        extra_services = [
            ('SRV-021', 'ECG Test', 'ecg', Decimal('500')),
            ('SRV-022', 'Ultrasound Abdomen', 'ultrasound', Decimal('800')),
            ('SRV-023', 'Ultrasound Pelvic', 'ultrasound', Decimal('900')),
            ('SRV-024', 'X-Ray Chest', 'xray', Decimal('300')),
            ('SRV-025', 'X-Ray Limbs', 'xray', Decimal('250')),
            ('SRV-026', 'CT Scan Head', 'radiology', Decimal('3000')),
            ('SRV-027', 'MRI Brain', 'radiology', Decimal('5000')),
            ('SRV-028', 'MRI Spine', 'radiology', Decimal('4500')),
            ('SRV-029', 'Dental Consultation', 'opd', Decimal('200')),
            ('SRV-030', 'ENT Consultation', 'opd', Decimal('200')),
            ('SRV-031', 'Dermatology Consultation', 'opd', Decimal('150')),
            ('SRV-032', 'Psychiatry Consultation', 'opd', Decimal('250')),
            ('SRV-033', 'Physiotherapy Session', 'procedure', Decimal('500')),
            ('SRV-034', 'Minor Surgery', 'procedure', Decimal('2000')),
            ('SRV-035', 'Major Surgery Fee', 'procedure', Decimal('5000')),
            ('SRV-036', 'Blood Transfusion Fee', 'procedure', Decimal('1500')),
            ('SRV-037', 'ICU Bed Day', 'procedure', Decimal('5000')),
            ('SRV-038', 'NICU Bed Day', 'procedure', Decimal('4000')),
            ('SRV-039', 'Ventilator Day', 'procedure', Decimal('3000')),
            ('SRV-040', 'Ambulance Service', 'other', Decimal('1000')),
        ]
        for code, name, cat, price in extra_services:
            if not HospitalService.objects.filter(code=code).exists():
                HospitalService.objects.create(
                    code=code, name=name, category=cat,
                    price=price, department=dept_map.get('General Medicine'),
                    is_active=True,
                )
        self.stdout.write(f'  Services total: {HospitalService.objects.count()}\n')

        # ===== 3. EXPAND LAB CATALOG =====
        self.stdout.write('Adding more lab tests...\n')
        extra_lab = [
            ('LC-021', 'Liver Function Test (LFT)', Decimal('350'), 'General Medicine'),
            ('LC-022', 'Kidney Function Test (KFT)', Decimal('400'), 'General Medicine'),
            ('LC-023', 'Serum Electrolytes', Decimal('250'), 'General Medicine'),
            ('LC-024', 'ESR', Decimal('100'), 'General Medicine'),
            ('LC-025', 'CRP Quantitative', Decimal('200'), 'General Medicine'),
            ('LC-026', 'D-Dimer', Decimal('600'), 'Cardiology'),
            ('LC-027', 'Troponin I', Decimal('500'), 'Cardiology'),
            ('LC-028', 'Urine Culture', Decimal('300'), 'General Medicine'),
            ('LC-029', 'Stool Culture', Decimal('250'), 'General Medicine'),
            ('LC-030', 'Thyroid Panel (T3/T4/TSH)', Decimal('450'), 'Endocrinology'),
            ('LC-031', 'PSA', Decimal('400'), 'Urology'),
            ('LC-032', 'RA Factor', Decimal('200'), 'Orthopedics'),
            ('LC-033', 'ANF', Decimal('250'), 'Orthopedics'),
            ('LC-034', 'Serum Ferritin', Decimal('300'), 'General Medicine'),
            ('LC-035', 'Vitamin B12', Decimal('350'), 'General Medicine'),
            ('LC-036', 'Vitamin D', Decimal('400'), 'General Medicine'),
            ('LC-037', 'HIV Elisa', Decimal('500'), 'General Medicine'),
            ('LC-038', 'HBsAg', Decimal('300'), 'General Medicine'),
            ('LC-039', 'HCV Antibody', Decimal('400'), 'General Medicine'),
            ('LC-040', 'Widal Test', Decimal('150'), 'General Medicine'),
        ]
        for code, name, price, dept_name in extra_lab:
            if not LabCatalog.objects.filter(code=code).exists():
                LabCatalog.objects.create(
                    code=code, name=name, price=price,
                    department=dept_map.get(dept_name), is_active=True,
                )
        self.stdout.write(f'  Lab Catalog total: {LabCatalog.objects.count()}\n')

        # ===== 4. EXPAND RADILOGY CATALOG =====
        self.stdout.write('Adding more radiology tests...\n')
        extra_rad = [
            ('RC-013', 'X-Ray Skull', 'xray', Decimal('350')),
            ('RC-014', 'X-Ray Spine Cervical', 'xray', Decimal('400')),
            ('RC-015', 'X-Ray Spine Lumbar', 'xray', Decimal('400')),
            ('RC-016', 'X-Ray Pelvis', 'xray', Decimal('350')),
            ('RC-017', 'X-Ray Abdomen', 'xray', Decimal('300')),
            ('RC-018', 'CT Scan Chest', 'ct', Decimal('3500')),
            ('RC-019', 'CT Scan Abdomen', 'ct', Decimal('4000')),
            ('RC-020', 'MRI Knee', 'mri', Decimal('4000')),
            ('RC-021', 'MRI Shoulder', 'mri', Decimal('4500')),
            ('RC-022', 'Doppler Carotid', 'ultrasound', Decimal('1200')),
            ('RC-023', 'Doppler Lower Limb', 'ultrasound', Decimal('1500')),
            ('RC-024', 'Mammography', 'ultrasound', Decimal('2000')),
        ]
        for code, name, img_type, price in extra_rad:
            if not RadiologyCatalog.objects.filter(code=code).exists():
                RadiologyCatalog.objects.create(
                    code=code, name=name, imaging_type=img_type,
                    price=price, is_active=True,
                )
        self.stdout.write(f'  Radiology Catalog total: {RadiologyCatalog.objects.count()}\n')

        # ===== 5. ADD 10 MORE PATIENTS (total 22) =====
        self.stdout.write('Adding 10 more patients...\n')
        patients_data = [
            ('Ramesh', 'Thapa', 'Male', 45, 'years', '9801111111', 'A+', 'Kathmandu'),
            ('Sita', 'Sharma', 'Female', 32, 'years', '9802222222', 'O+', 'Bhaktapur'),
            ('Hari', 'Magar', 'Male', 60, 'years', '9803333333', 'B+', 'Lalitpur'),
            ('Gita', 'Gurung', 'Female', 28, 'years', '9804444444', 'AB+', 'Pokhara'),
            ('Kumar', 'Rai', 'Male', 55, 'years', '9805555555', 'A-', 'Chitwan'),
            ('Anita', 'Tamang', 'Female', 38, 'years', '9806666666', 'O-', 'Nuwakot'),
            ('Bishnu', 'Sherpa', 'Male', 42, 'years', '9807777777', 'B-', 'Sindhupalchok'),
            ('Kamala', 'Yadav', 'Female', 50, 'years', '9808888888', 'AB-', 'Dhanusha'),
            ('Prakash', 'Chhetri', 'Male', 65, 'years', '9809999999', 'A+', 'Kaski'),
            ('Maya', 'Poudel', 'Female', 24, 'years', '9810000000', 'O+', 'Parbat'),
        ]
        province_bagmati = Province.objects.filter(name='Bagmati').first()
        district_ktm = District.objects.filter(name__icontains='Kathmandu', province=province_bagmati).first()
        reg_user = User.objects.filter(role='registration').first()
        counter_user = User.objects.filter(role='cash_counter').first()
        admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role='super_admin').first()

        new_patients = []
        for first, last, gender, age, age_type, phone, blood, district_name in patients_data:
            if not Patient.objects.filter(phone=phone).exists():
                p = Patient.objects.create(
                    first_name=first, last_name=last, gender=gender,
                    age_value=age, age_type=age_type, phone=phone,
                    blood_group=blood, address_line=district_name,
                    province=province_bagmati, district=district_ktm,
                    municipality=district_name, ward_number='5',
                    registered_by=reg_user, registration_source='counter',
                    is_new_patient=True,
                )
                new_patients.append(p)
        self.stdout.write(f'  Patients total: {Patient.objects.count()}\n')

        # ===== 6. ADD MORE OPD VISITS =====
        self.stdout.write('Adding 10 more OPD visits...\n')
        doctors = list(Doctor.objects.all())
        departments = list(Department.objects.all())
        today = timezone.now().date()
        all_patients = list(Patient.objects.all())

        for i, p in enumerate(new_patients[:10]):
            doc = doctors[i % len(doctors)]
            dept = departments[i % len(departments)]
            visit_date = timezone.now() - timedelta(days=random.randint(1, 30))
            token = OPDVisit.objects.filter(visit_date__date=visit_date.date()).count() + 1
            visit = OPDVisit.objects.create(
                patient=p, doctor=doc, department=dept,
                token_number=token + i,
                registration_fee=Decimal('100'),
                payment_method=random.choice(['cash', 'esewa']),
                visit_type='new',
                status=random.choice(['completed', 'completed', 'completed', 'in_progress']),
                created_by=reg_user,
            )
            # Force visit_date to past
            OPDVisit.objects.filter(pk=visit.pk).update(visit_date=visit_date)
        self.stdout.write(f'  OPD Visits total: {OPDVisit.objects.count()}\n')

        # ===== 7. ADD MORE BILLS (10+ with eSewa payments) =====
        self.stdout.write('Adding 10 more bills (some with eSewa payment)...\n')
        services = list(HospitalService.objects.all())
        for i, p in enumerate(all_patients[2:12]):
            if not Bill.objects.filter(patient=p).exists() or Bill.objects.filter(patient=p).count() < 2:
                bill = Bill.objects.create(
                    patient=p,
                    payment_method=random.choice(['cash', 'cash', 'esewa', 'esewa', 'cash']),
                    discount_type='none',
                    created_by=counter_user,
                    paid=True,
                )
                total = Decimal('0')
                for svc in random.sample(services, min(3, len(services))):
                    BillItem.objects.create(
                        bill=bill, service=svc,
                        service_name=svc.name, service_code=svc.code,
                        service_price=svc.price, quantity=1,
                        item_total=svc.price,
                    )
                    total += svc.price
                bill.total_amount = total
                bill.net_amount = total
                bill.save()
                # Set past date
                Bill.objects.filter(pk=bill.pk).update(created_at=timezone.now() - timedelta(days=random.randint(1, 20)))
        self.stdout.write(f'  Bills total: {Bill.objects.count()}\n')

        # ===== 8. ADD MORE LAB TEST REQUESTS (10+) =====
        self.stdout.write('Adding 10 more lab test requests...\n')
        lab_catalogs = list(LabCatalog.objects.all())
        visits = list(OPDVisit.objects.all())
        for i, p in enumerate(all_patients[:10]):
            visit = visits[i] if i < len(visits) else None
            doc = doctors[i % len(doctors)]
            catalog = lab_catalogs[i % len(lab_catalogs)]
            statuses = ['pending', 'sample_collected', 'testing', 'completed', 'completed', 'completed', 'completed', 'completed', 'pending', 'completed']
            req = LabTestRequest.objects.create(
                patient=p, consultation=None,
                doctor=doc, test_name=catalog.name,
                priority=random.choice(['routine', 'routine', 'urgent', 'emergency']),
                status=statuses[i % len(statuses)],
                result_notes='Normal values observed' if statuses[i] == 'completed' else '',
            )
            if statuses[i] == 'completed':
                LabTestRequest.objects.filter(pk=req.pk).update(completed_at=timezone.now() - timedelta(days=random.randint(1, 10)))
        self.stdout.write(f'  Lab Requests total: {LabTestRequest.objects.count()}\n')

        # ===== 9. ADD MORE RADILOGY REQUESTS (10+) =====
        self.stdout.write('Adding 10 more radiology requests...\n')
        rad_catalogs = list(RadiologyCatalog.objects.all())
        for i, p in enumerate(all_patients[:10]):
            doc = doctors[i % len(doctors)]
            catalog = rad_catalogs[i % len(rad_catalogs)]
            statuses = ['requested', 'scheduled', 'in_progress', 'completed', 'completed', 'completed', 'completed', 'completed', 'requested', 'completed']
            req = RadiologyRequest.objects.create(
                patient=p, consultation=None,
                doctor=doc, imaging_type=catalog.imaging_type,
                custom_type=catalog.name,
                priority=random.choice(['routine', 'routine', 'urgent']),
                status=statuses[i % len(statuses)],
                findings='No abnormality detected' if statuses[i] == 'completed' else '',
            )
            if statuses[i] == 'completed':
                RadiologyRequest.objects.filter(pk=req.pk).update(completed_at=timezone.now() - timedelta(days=random.randint(1, 10)))
        self.stdout.write(f'  Radiology Requests total: {RadiologyRequest.objects.count()}\n')

        # ===== 10. ADD MORE CONSULTATIONS (10+) =====
        self.stdout.write('Adding 10 more consultations...\n')
        for i, p in enumerate(all_patients[:10]):
            visit = OPDVisit.objects.filter(patient=p, status='completed').first()
            if visit and not Consultation.objects.filter(visit=visit).exists():
                doc = visit.doctor or doctors[0]
                consultation = Consultation.objects.create(
                    visit=visit, doctor=doc,
                    diagnosis=random.choice(['Acute Bronchitis', 'Hypertension', 'Diabetes Type 2', 'Gastritis', 'Urinary Tract Infection', 'Pneumonia', 'Malaria', 'Typhoid', 'Appendicitis', 'Fracture']),
                    clinical_notes='Patient presented with symptoms. Examination conducted.',
                    follow_up_date=today + timedelta(days=7),
                )
                # Add prescription
                pres = Prescription.objects.create(
                    medicine_name=random.choice(['Paracetamol 500mg', 'Amoxicillin 500mg', 'Omeprazole 20mg']),
                    dosage=random.choice(['1 tab twice daily', '1 cap three times daily', '1 tab once daily']),
                    frequency='Daily', duration='7 days',
                )
                consultation.prescriptions.add(pres)
        self.stdout.write(f'  Consultations total: {Consultation.objects.count()}\n')

        # ===== 11. ADD MORE PHARMACY SALES (10+) =====
        self.stdout.write('Adding 10 more pharmacy sales...\n')
        meds = list(Medicine.objects.all())
        for i, p in enumerate(all_patients[:10]):
            sale = PharmacySale.objects.create(
                patient=p,
                payment_method=random.choice(['cash', 'cash', 'esewa']),
                counter_staff=User.objects.filter(role='pharmacy').first(),
            )
            total = Decimal('0')
            for med in random.sample(meds, min(2, len(meds))):
                qty = random.randint(1, 5)
                SaleItem.objects.create(
                    sale=sale, medicine=med,
                    quantity=qty, price_at_sale=med.price,
                    total=med.price * qty,
                )
                total += med.price * qty
            sale.total_amount = total
            sale.discount = Decimal('0')
            sale.final_amount = total
            sale.save()
            PharmacySale.objects.filter(pk=sale.pk).update(sale_date=timezone.now() - timedelta(days=random.randint(1, 15)))
        self.stdout.write(f'  Pharmacy Sales total: {PharmacySale.objects.count()}\n')

        # ===== 12. ADD MORE PATIENT INSURANCE (10+) =====
        self.stdout.write('Adding 10 more patient insurance records...\n')
        insurers = list(Insurer.objects.all())
        for i, p in enumerate(all_patients[:10]):
            if not PatientInsurance.objects.filter(patient=p).exists():
                ins = insurers[i % len(insurers)]
                PatientInsurance.objects.create(
                    patient=p, insurer=ins,
                    policy_number=f'POL-{ins.code}-{p.patient_id}',
                    coverage_percentage=Decimal(str(random.choice([50, 60, 70, 80, 90]))),
                    is_active=True,
                )
        self.stdout.write(f'  Patient Insurance total: {PatientInsurance.objects.count()}\n')

        # ===== 13. ADD MORE INSURANCE CLAIMS (10+) =====
        self.stdout.write('Adding 10 more insurance claims...\n')
        for i, p in enumerate(all_patients[:10]):
            pi = PatientInsurance.objects.filter(patient=p).first()
            if pi:
                claim = InsuranceClaim.objects.create(
                    patient=p, insurance=pi,
                    amount=Decimal(str(random.randint(500, 5000))),
                    approved_amount=Decimal(str(random.randint(200, 4000))) if random.random() > 0.3 else Decimal('0'),
                    status=random.choice(['pending', 'pending', 'approved', 'approved', 'settled', 'rejected', 'pending', 'approved', 'settled', 'pending']),
                    submitted_by=User.objects.filter(role='insurance').first(),
                )
                InsuranceClaim.objects.filter(pk=claim.pk).update(created_at=timezone.now() - timedelta(days=random.randint(1, 20)))
        self.stdout.write(f'  Insurance Claims total: {InsuranceClaim.objects.count()}\n')

        # ===== 14. ADD MORE ADMISSIONS (5 more) =====
        self.stdout.write('Adding 5 more admissions...\n')
        available_beds = list(Bed.objects.filter(is_occupied=False))
        for i, p in enumerate(all_patients[5:10]):
            if available_beds and i < len(available_beds):
                bed = available_beds[i]
                doc = doctors[i % len(doctors)]
                ward = bed.ward
                adm = Admission.objects.create(
                    patient=p, doctor=doc,
                    ward=ward, bed=bed,
                    diagnosis=random.choice(['Acute Pneumonia', 'Chronic Kidney Disease', 'Fracture Femur', 'Severe Dengue', 'Post-Op Recovery']),
                    created_by=User.objects.filter(role='admission').first(),
                )
                bed.is_occupied = True
                bed.save()
        self.stdout.write(f'  Admissions total: {Admission.objects.count()}\n')

        # ===== 15. ADD DISCHARGE SUMMARIES (3+) =====
        self.stdout.write('Adding discharge summaries...\n')
        discharged_admissions = Admission.objects.filter(status='discharged')
        for adm in discharged_admissions:
            if not DischargeSummary.objects.filter(admission=adm).exists():
                DischargeSummary.objects.create(
                    admission=adm, patient=adm.patient,
                    attending_doctor=adm.doctor,
                    admission_diagnosis=adm.diagnosis,
                    final_diagnosis=adm.diagnosis,
                    chief_complaint='Presenting symptoms on admission',
                    condition_at_discharge='improved',
                    discharge_instructions='Continue medication, follow-up in 7 days',
                    follow_up_date=today + timedelta(days=7),
                    medications_at_discharge='Continue prescribed medications',
                    prepared_by=admin_user,
                )
        # Create discharge summaries for current admitted too (mark some as discharged)
        for adm in Admission.objects.filter(status='admitted')[:3]:
            adm.status = 'discharged'
            adm.save()
            bed = adm.bed
            if bed:
                bed.is_occupied = False
                bed.save()
            DischargeSummary.objects.create(
                admission=adm, patient=adm.patient,
                attending_doctor=adm.doctor,
                admission_diagnosis=adm.diagnosis,
                final_diagnosis=adm.diagnosis,
                chief_complaint='Presenting symptoms',
                condition_at_discharge='improved',
                discharge_instructions='Follow-up in 1 week',
                follow_up_date=today + timedelta(days=7),
                medications_at_discharge='Continue medications',
                prepared_by=admin_user,
            )
        self.stdout.write(f'  Discharge Summaries total: {DischargeSummary.objects.count()}\n')

        # ===== 16. ADD APPOINTMENTS (10+) =====
        self.stdout.write('Adding 10 appointments...\n')
        for i, p in enumerate(all_patients[:10]):
            doc = doctors[i % len(doctors)]
            dept = doc.department or departments[0]
            Appointment.objects.create(
                patient=p, doctor=doc, department=dept,
                appointment_date=today + timedelta(days=random.randint(1, 7)),
                appointment_time=time(random.randint(9, 14), random.choice([0, 30])),
                status=random.choice(['pending', 'confirmed', 'confirmed', 'confirmed', 'pending']),
                payment_status=random.choice(['unpaid', 'paid', 'unpaid', 'paid', 'unpaid']),
            )
        self.stdout.write(f'  Appointments total: {Appointment.objects.count()}\n')

        # ===== 17. ADD NURSING NOTES (10+) =====
        self.stdout.write('Adding 10 nursing notes...\n')
        admitted = Admission.objects.filter(status='admitted')
        nurse = User.objects.filter(role='nursing').first()
        for i, adm in enumerate(admitted[:5]):
            p = adm.patient
            for j in range(2):
                NursingNote.objects.create(
                    patient=p, note_type=random.choice(['nursing_note', 'vital_signs', 'progress', 'medication_admin']),
                    content=f'Patient {p.full_name} vitals stable. BP: {random.randint(100,140)}/{random.randint(60,90)}, Temp: {random.randint(96,101)}°F, Pulse: {random.randint(60,90)} bpm',
                    vital_bp=f'{random.randint(100,140)}/{random.randint(60,90)}',
                    vital_temp=f'{random.randint(96,101)}°F',
                    vital_pulse=str(random.randint(60, 90)),
                    vital_resp=str(random.randint(12, 20)),
                    created_by=nurse,
                )
        self.stdout.write(f'  Nursing Notes total: {NursingNote.objects.count()}\n')

        # ===== 18. ADD SURGERIES (10+) =====
        self.stdout.write('Adding 10 surgeries...\n')
        surgery_types = ['Appendectomy', 'Cholecystectomy', 'Hernia Repair', 'Knee Replacement', 'Cataract Surgery',
                         'Tonsillectomy', 'Hysterectomy', 'Fracture Repair', 'Heart Bypass', 'Laparotomy']
        statuses = ['scheduled', 'scheduled', 'in_progress', 'completed', 'completed', 'completed', 'completed', 'scheduled', 'scheduled', 'completed']
        for i, p in enumerate(all_patients[:10]):
            doc = doctors[i % len(doctors)]
            Surgery.objects.create(
                patient=p, doctor=doc,
                surgery_type=surgery_types[i % len(surgery_types)],
                priority=random.choice(['routine', 'routine', 'urgent', 'emergency']),
                status=statuses[i % len(statuses)],
                clinical_notes=f'Patient {p.full_name} scheduled for {surgery_types[i % len(surgery_types)]}',
                planned_date=today + timedelta(days=random.randint(1, 14)),
                created_by=admin_user,
            )
        self.stdout.write(f'  Surgeries total: {Surgery.objects.count()}\n')

        # ===== 19. ADD BLOOD REQUESTS (10+) =====
        self.stdout.write('Adding 10 blood requests...\n')
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        statuses_blood = ['pending', 'pending', 'issued', 'completed', 'completed', 'pending', 'issued', 'completed', 'pending', 'completed']
        for i, p in enumerate(all_patients[:10]):
            doc = doctors[i % len(doctors)]
            BloodRequest.objects.create(
                patient=p, doctor=doc,
                blood_group=blood_groups[i % len(blood_groups)],
                units_required=random.randint(1, 3),
                urgency=random.choice(['routine', 'routine', 'urgent', 'emergency']),
                status=statuses_blood[i % len(statuses_blood)],
                issued_units=random.randint(1, 2) if statuses_blood[i] in ('issued', 'completed') else 0,
            )
        self.stdout.write(f'  Blood Requests total: {BloodRequest.objects.count()}\n')

        # ===== 20. ADD MORE MEDICAL RECORDS (20+) =====
        self.stdout.write('Adding more medical records...\n')
        record_types = ['doctor_note', 'nursing_note', 'lab_report', 'radiology_report', 'pharmacy_record',
                        'blood_bank_record', 'admission_record', 'ot_record', 'insurance_doc', 'uploaded_pdf']
        for i, p in enumerate(all_patients[:10]):
            for j, rtype in enumerate(record_types[:3]):
                if MedicalRecord.objects.filter(patient=p, record_type=rtype).count() < 2:
                    MedicalRecord.objects.create(
                        patient=p, department=rtype.split('_')[0],
                        record_type=rtype,
                        title=f'{rtype.replace("_"," ").title()} - {p.patient_id}',
                        summary=f'Auto-attached {rtype} record for patient {p.full_name}',
                        uploaded_by='system', staff_name='Hamro Hospital System',
                    )
        self.stdout.write(f'  Medical Records total: {MedicalRecord.objects.count()}\n')

        # ===== 21. ADD MORE TESTIMONIALS =====
        self.stdout.write('Adding more testimonials...\n')
        extra_testimonials = [
            ('Dr. Prakash Sharma', 'Neurologist', 'Hamro Hospital saved my patient with timely intervention. Excellent facilities!'),
            ('Mrs. Kamala Thapa', 'Patient Family', 'The nursing staff was incredibly caring during my mother\'s stay.'),
            ('Mr. Rajendra KC', 'Health Insurance Provider', 'The insurance process was smooth and transparent. Great hospital.'),
            ('Dr. Susan Limbu', 'General Practitioner', 'I refer all my patients here. The diagnostic lab is outstanding.'),
            ('Mr. Deepak Maharjan', 'Patient', 'Fast registration, clear bills, and helpful staff. Thank you!'),
            ('Ms. Aarati Poudel', 'Patient', 'The online portal made it easy to check my lab results from home.'),
        ]
        for name, role, content in extra_testimonials:
            if not Testimonial.objects.filter(name=name).exists():
                Testimonial.objects.create(name=name, role=role, content=content, is_active=True)
        self.stdout.write(f'  Testimonials total: {Testimonial.objects.count()}\n')

        # ===== 22. ADD DISEASE INFO =====
        self.stdout.write('Adding more disease info...\n')
        diseases = [
            ('Dengue Fever', 'Dengue is a mosquito-borne viral infection causing flu-like illness. Prevention: mosquito control, use repellent.'),
            ('Typhoid', 'Typhoid is a bacterial infection from contaminated food/water. Symptoms: fever, weakness, stomach pain. Vaccine available.'),
            ('Tuberculosis (TB)', 'TB is a bacterial disease affecting lungs. Nepal has high TB burden. Free treatment available at Hamro Hospital.'),
            ('Hepatitis B', 'Hepatitis B is a liver infection. Chronic cases lead to cirrhosis. Vaccination is the best prevention.'),
            ('Malaria', 'Malaria is transmitted by Anopheles mosquitoes. Symptoms: fever, chills, headache. Use mosquito nets in endemic areas.'),
            ('Cholera', 'Cholera causes severe watery diarrhea and dehydration. ORS treatment is critical. Clean water prevents it.'),
            ('HIV/AIDS', 'HIV weakens the immune system. Nepal has concentrated epidemic. Free testing at Hamro Hospital.'),
        ]
        for name, desc in diseases:
            if not DiseaseInfo.objects.filter(name=name).exists():
                DiseaseInfo.objects.create(name=name, description=desc, is_active=True)
        self.stdout.write(f'  Disease Info total: {DiseaseInfo.objects.count()}\n')

        # ===== 23. EXPAND TO 10+ — ADD MORE WARDS =====
        self.stdout.write('Adding more wards to reach 10+...\n')
        extra_wards = [
            ('General Ward B', 'General Medicine', 2),
            ('Surgical Ward B', 'Surgery', 2),
            ('Pediatric Ward B', 'Pediatrics', 3),
            ('Oncology Ward', 'Oncology', 4),
        ]
        for wname, dept_name, floor in extra_wards:
            dept = Department.objects.filter(name__icontains=dept_name).first()
            if not Ward.objects.filter(name=wname).exists():
                w = Ward.objects.create(name=wname, department=dept, floor=floor, is_active=True)
                for bn in range(1, 9):
                    Bed.objects.create(ward=w, bed_number=f'{wname[:3].upper()}-{bn:02d}', is_occupied=False, bed_type='general')
        self.stdout.write(f'  Wards total: {Ward.objects.count()}\n')
        self.stdout.write(f'  Beds total: {Bed.objects.count()}\n')

        # ===== 24. EXPAND TO 10+ — ADD MORE ADMISSSIONS =====
        self.stdout.write('Adding more admissions to reach 10+...\n')
        all_patients = list(Patient.objects.all())
        doctors = list(Doctor.objects.all())
        wards = list(Ward.objects.filter(is_active=True))
        admin_user = User.objects.filter(role='admission').first() or User.objects.filter(is_superuser=True).first()
        current_admissions = Admission.objects.count()
        needed_admissions = max(0, 12 - current_admissions)
        for i in range(needed_admissions):
            p = all_patients[i % len(all_patients)]
            doc = doctors[i % len(doctors)]
            ward = wards[i % len(wards)]
            bed = Bed.objects.filter(ward=ward, is_occupied=False).first()
            if bed:
                bed.is_occupied = True
                bed.save()
            diagnoses = ['Acute Appendicitis', 'Pneumonia', 'Fracture - Femur', 'Acute Kidney Injury',
                         'Severe Anemia', 'Severe Pneumonia', 'Acute Pancreatitis', 'Traumatic Brain Injury', 'Septicemia']
            Admission.objects.create(
                patient=p, doctor=doc, ward=ward, bed=bed,
                diagnosis=diagnoses[i % len(diagnoses)],
                treatment='Admitted for observation and treatment',
                status='admitted',
                admission_fee=random.choice([500, 1000, 1500, 2000]),
                created_by=admin_user,
            )
        self.stdout.write(f'  Admissions total: {Admission.objects.count()}\n')

        # ===== 25. EXPAND TO 10+ — DISCHARGE MORE + CREATE DISCHARGE SUMMARIES =====
        self.stdout.write('Discharging admissions to create discharge summaries (target: 10+)...\n')
        admitted = list(Admission.objects.filter(status='admitted'))
        needed_discharges = max(0, 7 - DischargeSummary.objects.count())
        conditions = ['improved', 'improved', 'stable', 'improved', 'stable', 'improved', 'improved']
        for i, adm in enumerate(admitted[:needed_discharges]):
            adm.status = 'discharged'
            adm.discharge_date = timezone.now() - timedelta(days=random.randint(1, 5))
            adm.save()
            if adm.bed:
                adm.bed.is_occupied = False
                adm.bed.save()
            if not DischargeSummary.objects.filter(admission=adm).exists():
                DischargeSummary.objects.create(
                    admission=adm, patient=adm.patient,
                    attending_doctor=adm.doctor,
                    admission_diagnosis=adm.diagnosis,
                    final_diagnosis=adm.diagnosis,
                    chief_complaint='Presenting symptoms on admission',
                    history_of_present_illness=f'Patient presented with {adm.diagnosis}. History documented.',
                    examination_findings='General examination: conscious, oriented. Vitals stable.',
                    investigations='Relevant lab and imaging investigations completed.',
                    treatment_given='Treatment administered as per protocol. Patient responded well.',
                    condition_at_discharge=conditions[i % len(conditions)],
                    discharge_instructions='Continue medication, follow-up in 7 days, avoid strenuous activity',
                    follow_up_date=today + timedelta(days=7),
                    follow_up_instructions='Follow-up in OPD, bring all reports',
                    medications_at_discharge='Continue prescribed medications for 2 weeks',
                    prepared_by=admin_user,
                )
        # Also ensure at least 6 active admissions remain
        remaining_active = Admission.objects.filter(status='admitted').count()
        if remaining_active < 6:
            for i in range(6 - remaining_active):
                p = all_patients[i % len(all_patients)]
                doc = doctors[i % len(doctors)]
                ward = wards[i % len(wards)]
                bed = Bed.objects.filter(ward=ward, is_occupied=False).first()
                if bed:
                    bed.is_occupied = True
                    bed.save()
                Admission.objects.create(
                    patient=p, doctor=doc, ward=ward, bed=bed,
                    diagnosis=random.choice(['Severe Pneumonia', 'Acute Pancreatitis', 'Traumatic Brain Injury', 'Septicemia']),
                    treatment='Admitted for observation and treatment',
                    status='admitted',
                    admission_fee=random.choice([500, 1000, 1500, 2000]),
                    created_by=admin_user,
                )
        self.stdout.write(f'  Discharge Summaries total: {DischargeSummary.objects.count()}\n')
        self.stdout.write(f'  Active admissions: {Admission.objects.filter(status=\"admitted\").count()}\n')
        self.stdout.write(f'  Discharged admissions: {Admission.objects.filter(status=\"discharged\").count()}\n')

        # ===== 26. EXPAND TO 10+ — ADD MORE NURSING NOTES =====
        self.stdout.write('Adding more nursing notes (target: 10+)...\n')
        nurse = User.objects.filter(role='nursing').first()
        current_notes = NursingNote.objects.count()
        needed_notes = max(0, 12 - current_notes)
        admitted_now = list(Admission.objects.filter(status='admitted'))
        discharged_now = list(Admission.objects.filter(status='discharged'))
        note_count = 0
        for adm in admitted_now[:3]:
            p = adm.patient
            for j in range(2):
                if note_count < needed_notes:
                    NursingNote.objects.create(
                        patient=p,
                        note_type=random.choice(['nursing_note', 'vital_signs', 'progress', 'medication_admin', 'observation']),
                        content=f'Patient {p.full_name} - {random.choice(["Vitals stable", "Condition improving", "Medication administered", "Patient comfortable", "Wound healing well"])}. BP: {random.randint(100,140)}/{random.randint(60,90)}, Temp: {random.randint(96,101)}°F, Pulse: {random.randint(60,90)} bpm',
                        vital_bp=f'{random.randint(100,140)}/{random.randint(60,90)}',
                        vital_temp=f'{random.randint(96,101)}°F',
                        vital_pulse=str(random.randint(60, 90)),
                        vital_resp=str(random.randint(12, 20)),
                        created_by=nurse,
                    )
                    note_count += 1
        for adm in discharged_now[:3]:
            p = adm.patient
            if note_count < needed_notes:
                NursingNote.objects.create(
                    patient=p,
                    note_type='nursing_note',
                    content=f'Discharge note for {p.full_name}. Patient educated on discharge instructions.',
                    created_by=nurse,
                )
                note_count += 1
        self.stdout.write(f'  Nursing Notes total: {NursingNote.objects.count()}\n')

        # ===== 27. EXPAND TO 10+ — ADD MORE MEDICAL RECORDS =====
        self.stdout.write('Adding more medical records (target: 10+)...\n')
        for p in all_patients[:15]:
            for rtype in ['lab_report', 'radiology_report', 'admission_record']:
                if MedicalRecord.objects.filter(patient=p, record_type=rtype).count() < 1:
                    MedicalRecord.objects.create(
                        patient=p,
                        department=rtype.split('_')[0],
                        record_type=rtype,
                        title=f'{rtype.replace("_"," ").title()} - {p.patient_id}',
                        summary=f'Auto-attached {rtype} record for patient {p.full_name}',
                        uploaded_by='system',
                        staff_name='Hamro Hospital System',
                    )
        self.stdout.write(f'  Medical Records total: {MedicalRecord.objects.count()}\n')

        self.stdout.write('\n=== SEED EXPANSION COMPLETE ===\n')
