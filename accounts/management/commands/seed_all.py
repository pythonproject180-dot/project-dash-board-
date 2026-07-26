from django.core.management.base import BaseCommand
from accounts.models import User, Province, District, AuditLog
from departments.models import Department
from doctors.models import Doctor, DoctorQuota
from patients.models import Patient, OPDVisit
from billing.models import HospitalService, Bill, BillItem
from pharmacy.models import Medicine, PharmacySale, SaleItem
from admissions.models import Ward, Bed, Admission
from insurance.models import Insurer, PatientInsurance, InsuranceClaim
from consultations.models import LabTestRequest, RadiologyRequest, Consultation, Prescription
from website.models import Testimonial, GalleryImage, DiseaseInfo
from nursing.models import NursingNote
from operation_theatre.models import Surgery
from blood_bank.models import BloodRequest
from medical_records.models import MedicalRecord
from patient_portal.models import PortalUser
from laboratory.models import LabCatalog
from radiology.models import RadiologyCatalog
from django.utils import timezone
from django.conf import settings

ROLES = {
    'admin': 'super_admin', 'registration': 'registration', 'cashier': 'cash_counter',
    'doctor': 'doctor', 'pharmacy': 'pharmacy', 'laboratory': 'laboratory',
    'radiology': 'radiology', 'insurance': 'insurance', 'admission': 'admission',
    'nursing': 'nursing', 'operationtheatre': 'operation_theatre',
    'bloodbank': 'blood_bank', 'accounts': 'accounts', 'medicalrecords': 'medical_records',
}

PROVINCES = ['Bagmati', 'Madhesh', 'Lumbini', 'Karnali', 'Sudurpashchim', 'Koshi', 'Gandaki']

DISTRICTS_MAP = {
    'Bagmati': ['Kathmandu', 'Lalitpur', 'Bhaktapur', 'Chitwan', 'Dhading', 'Nuwakot', 'Sindhulpalchok', 'Rasuwa', 'Makwanpur', 'Parsa', 'Bara', 'Rautahat', 'Sindhuli', 'Kavrepalanchok'],
    'Madhesh': ['Sarlahi', 'Mahottari', 'Dhanusha', 'Siraha', 'Saptari', 'Jhapa', 'Morang', 'Sunsari'],
    'Lumbini': ['Rupandehi', 'Nawalparasi', 'Palpa', 'Gulmi', 'Argakhanchi', 'Kapilvastu', 'Dang', 'Banke', 'Bardiya'],
    'Karnali': ['Surkhet', 'Jumla', 'Kalikot', 'Mugu', 'Humla', 'Dolpa', 'Dailekh', 'Jajarkot'],
    'Sudurpashchim': ['Doti', 'Achham', 'Bajhang', 'Bajura', 'Darchula', 'Kailali', 'Kanchanpur'],
    'Koshi': ['Taplejung', 'Panchthar', 'Ilam', 'Terhathum', 'Okhaldhunga', 'Udayapur', 'Sankhuwasabha', 'Bhojpur', 'Solukhumbu'],
    'Gandaki': ['Kaski', 'Lamjung', 'Gorkha', 'Tanahu', 'Syangja', 'Manang', 'Mustang', 'Parbat', 'Myagdi'],
}

DEPARTMENTS = [
    ('Emergency & Critical Care', '24/7 emergency and critical care services', 800),
    ('General Medicine', 'Internal medicine and general health consultations', 500),
    ('Cardiology', 'Heart and cardiovascular disease treatment', 1000),
    ('Orthopedics', 'Bone, joint, and musculoskeletal care', 800),
    ('Pediatrics', 'Child health and pediatric care', 500),
    ('Obstetrics & Gynecology', "Women's health, pregnancy, and childbirth", 700),
    ('Neurology', 'Brain and nervous system disorders', 900),
    ('Ophthalmology', 'Eye care and vision treatment', 600),
    ('ENT', 'Ear, nose, and throat care', 500),
    ('Dermatology', 'Skin, hair, and nail care', 500),
    ('Psychiatry', 'Mental health and counseling', 600),
    ('Urology', 'Urinary tract and kidney care', 700),
    ('Surgery', 'General and specialized surgery', 1000),
    ('Radiology', 'Diagnostic imaging services', 500),
    ('Laboratory', 'Pathology and diagnostic tests', 300),
]

SERVICES = [
    ('OPD-001', 'OPD Registration', 100, 'opd'),
    ('OPD-002', 'OPD Follow-up Registration', 50, 'opd'),
    ('LAB-001', 'Blood Test CBC', 300, 'laboratory'),
    ('LAB-002', 'Liver Function Test', 800, 'laboratory'),
    ('LAB-003', 'Kidney Function Test', 700, 'laboratory'),
    ('LAB-004', 'Blood Glucose Test', 200, 'laboratory'),
    ('LAB-005', 'Urine Analysis', 150, 'laboratory'),
    ('LAB-006', 'Thyroid Function Test', 900, 'laboratory'),
    ('LAB-007', 'Hemoglobin Test', 100, 'laboratory'),
    ('LAB-008', 'Widal Test', 250, 'laboratory'),
    ('RAD-001', 'X-Ray', 500, 'xray'),
    ('RAD-002', 'CT Scan', 3000, 'ct'),
    ('RAD-003', 'MRI', 5000, 'mri'),
    ('RAD-004', 'ECG', 300, 'ecg'),
    ('RAD-005', 'Ultrasound', 800, 'ultrasound'),
    ('RAD-006', 'Echo', 1200, 'echo'),
    ('SUR-001', 'Minor Surgery', 5000, 'procedure'),
    ('ADM-001', 'Admission Fee', 2000, 'other'),
    ('BB-001', 'Blood Transfusion', 1500, 'other'),
    ('PHR-001', 'Pharmacy Service', 100, 'pharmacy'),
]

LAB_CATALOG = [
    ('CBC', 'Complete Blood Count', 300),
    ('LFT', 'Liver Function Test', 800),
    ('KFT', 'Kidney Function Test', 700),
    ('GLU', 'Blood Glucose', 200),
    ('UA', 'Urine Analysis', 150),
    ('TFT', 'Thyroid Function Test', 900),
    ('HB', 'Hemoglobin', 100),
    ('WIDAL', 'Widal Test', 250),
    ('ESR', 'ESR Test', 150),
    ('CR', 'C-Reactive Protein', 400),
    ('HBV', 'Hepatitis B', 500),
    ('HCV', 'Hepatitis C', 600),
    ('HIV', 'HIV Test', 300),
    ('BT', 'Blood Typing', 200),
    ('PT', 'Prothrombin Time', 350),
    ('SPO2', 'Oxygen Saturation', 100),
    ('CULT', 'Blood Culture', 800),
    ('CSF', 'CSF Analysis', 900),
    ('STOOL', 'Stool Analysis', 150),
    ('SEMEN', 'Semen Analysis', 400),
]

RADIOLOGY_CATALOG = [
    ('XR-CHEST', 'Chest X-Ray', 500, 'xray'),
    ('XR-LIMB', 'Limb X-Ray', 400, 'xray'),
    ('XR-SPINE', 'Spine X-Ray', 600, 'xray'),
    ('CT-BRAIN', 'CT Brain', 3000, 'ct'),
    ('CT-ABD', 'CT Abdomen', 3500, 'ct'),
    ('MRI-BRAIN', 'MRI Brain', 5000, 'mri'),
    ('MRI-SPINE', 'MRI Spine', 6000, 'mri'),
    ('ECG-STD', 'Standard ECG', 300, 'ecg'),
    ('ECG-STRESS', 'Stress ECG', 800, 'ecg'),
    ('US-ABD', 'Abdominal Ultrasound', 800, 'ultrasound'),
    ('US-PREG', 'Pregnancy Ultrasound', 600, 'ultrasound'),
    ('ECHO-STD', 'Standard Echo', 1200, 'echo'),
]

MEDICINES = [
    ('MED-001', 'Paracetamol 500mg', 'Acetaminophen', 'Tablet', 5, 1000),
    ('MED-002', 'Amoxicillin 500mg', 'Amoxicillin', 'Capsule', 20, 500),
    ('MED-003', 'Omeprazole 20mg', 'Omeprazole', 'Capsule', 15, 300),
    ('MED-004', 'Metformin 500mg', 'Metformin', 'Tablet', 10, 800),
    ('MED-005', 'Amlodipine 5mg', 'Amlodipine', 'Tablet', 12, 500),
    ('MED-006', 'Insulin Injection', 'Insulin', 'Injection', 150, 100),
    ('MED-007', 'Diazepam 5mg', 'Diazepam', 'Tablet', 8, 200),
    ('MED-008', 'Aspirin 300mg', 'Aspirin', 'Tablet', 3, 1000),
    ('MED-009', 'Ciprofloxacin 500mg', 'Ciprofloxacin', 'Tablet', 25, 400),
    ('MED-010', 'Ibuprofen 400mg', 'Ibuprofen', 'Tablet', 6, 600),
]


class Command(BaseCommand):
    help = 'Seed the entire Hamro Hospital database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding Hamro Hospital database...\n')

        # Provinces & Districts
        for prov_name in PROVINCES:
            prov, _ = Province.objects.get_or_create(name=prov_name)
            for dist_name in DISTRICTS_MAP.get(prov_name, []):
                District.objects.get_or_create(name=dist_name.strip(), province=prov)
        self.stdout.write(f'  ✓ {Province.objects.count()} provinces, {District.objects.count()} districts\n')

        # Staff Accounts
        for username, role in ROLES.items():
            User.objects.get_or_create(
                username=username, defaults={
                    'role': role, 'is_staff': True, 'is_active_staff': True,
                    'first_name': role.replace('_', ' ').title(),
                }
            )
            user = User.objects.get(username=username)
            user.set_password('password123*#')
            user.save()
        self.stdout.write(f'  ✓ {len(ROLES)} staff accounts created (password: password123*#)\n')

        # Departments
        dept_objs = {}
        for name, desc, fee in DEPARTMENTS:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'description': desc, 'consultation_fee': fee})
            dept_objs[name] = dept
        self.stdout.write(f'  ✓ {Department.objects.count()} departments\n')

        # Doctors
        doctor_names = ['Ramesh Sharma', 'Sita Devi', 'Hari Prasad', 'Anita Kumari', 'Bikash Thapa',
                        'Maya Gurung', 'Rajendra Mishra', 'Pramila Rai', 'Krishna KC', 'Sunita Adhikari',
                        'Dipak Jha', 'Kamala Basnet', 'Arun Poudel', 'Binita Shah', 'Gopal Shrestha']
        doc_objs = []
        dept_list = list(dept_objs.values())
        for i, name in enumerate(doctor_names):
            dept = dept_list[i % len(dept_list)]
            doc, _ = Doctor.objects.get_or_create(name=name, defaults={
                'department': dept, 'qualification': 'MBBS, MD',
                'specialization': dept.name, 'consultation_fee': dept.consultation_fee,
                'phone': f'+977-98{10000000+i}', 'schedule': 'Mon-Fri 9AM-5PM',
            })
            doc_objs.append(doc)
        # Link doctor user account
        doctor_user = User.objects.get(username='doctor')
        if doc_objs:
            doc_objs[0].user_account = doctor_user
            doc_objs[0].save()
        self.stdout.write(f'  ✓ {Doctor.objects.count()} doctors\n')

        # Doctor Quotas — create OPD quotas for each doctor
        for i, doc in enumerate(doc_objs):
            for weekday in range(6):  # Mon-Sat
                max_p = 50 + (i % 3) * 10
                DoctorQuota.objects.get_or_create(
                    doctor=doc, weekday=weekday, defaults={
                        'max_patients': max_p,
                        'start_time': '09:00',
                        'end_time': '14:00',
                    }
                )
        self.stdout.write(f'  ✓ {DoctorQuota.objects.count()} doctor quotas\n')

        # Hospital Services with categories
        for code, name, price, category in SERVICES:
            HospitalService.objects.get_or_create(code=code, defaults={
                'name': name, 'price': price, 'category': category,
            })
        self.stdout.write(f'  ✓ {HospitalService.objects.count()} services\n')

        # Lab Catalog
        lab_dept = dept_objs.get('Laboratory')
        for code, name, price in LAB_CATALOG:
            LabCatalog.objects.get_or_create(code=code, defaults={
                'name': name, 'price': price, 'department': lab_dept,
            })
        self.stdout.write(f'  ✓ {LabCatalog.objects.count()} lab catalog entries\n')

        # Radiology Catalog
        for code, name, price, imaging_type in RADIOLOGY_CATALOG:
            RadiologyCatalog.objects.get_or_create(code=code, defaults={
                'name': name, 'price': price, 'imaging_type': imaging_type,
            })
        self.stdout.write(f'  ✓ {RadiologyCatalog.objects.count()} radiology catalog entries\n')

        # Medicines
        for code, name, generic, unit, price, stock in MEDICINES:
            Medicine.objects.get_or_create(code=code, defaults={
                'name': name, 'generic_name': generic, 'unit': unit,
                'price': price, 'stock_quantity': stock, 'minimum_stock': 10,
            })
        self.stdout.write(f'  ✓ {Medicine.objects.count()} medicines\n')

        # Insurers
        for name, code in [('Nepal Health Insurance', 'NHIF'), ('SBI General Insurance', 'SBI'), ('Prime Life Insurance', 'PRIME')]:
            Insurer.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write(f'  ✓ {Insurer.objects.count()} insurers\n')

        # Wards & Beds
        ward_names = ['General Ward A', 'General Ward B', 'ICU', 'Semi-Private Ward', 'Private Ward', 'Pediatric Ward', 'Maternity Ward']
        ward_objs = []
        for i, wn in enumerate(ward_names):
            ward, _ = Ward.objects.get_or_create(name=wn, defaults={
                'floor': i//3 + 1, 'department': dept_list[i % len(dept_list)]
            })
            ward_objs.append(ward)
            for j in range(8):
                bed_types = ['general', 'general', 'general', 'general', 'general', 'general',
                             'semi_private', 'semi_private']
                if wn == 'ICU':
                    bed_types = ['icu'] * 8
                Bed.objects.get_or_create(ward=ward, bed_number=f'{wn[:3]}-{j+1}', defaults={
                    'bed_type': bed_types[j % len(bed_types)]
                })
        self.stdout.write(f'  ✓ {Ward.objects.count()} wards, {Bed.objects.count()} beds\n')

        # Testimonials
        for name, role, content in [
            ('Ramesh Sharma', 'Patient, Kathmandu', 'Excellent care and professional doctors. Highly recommended!'),
            ('Sita Devi', 'Patient, Pokhara', 'The staff was very caring and the treatment was affordable.'),
            ('Hari Prasad', 'Patient, Chitwan', 'Quick service and clean facilities. Very satisfied.'),
            ('Anita Kumari', 'Patient, Lalitpur', 'My surgery was successful and the recovery was well-managed.'),
        ]:
            Testimonial.objects.get_or_create(name=name, defaults={'role': role, 'content': content})
        self.stdout.write(f'  ✓ {Testimonial.objects.count()} testimonials\n')

        # Disease Info
        for name, desc in [
            ('Diabetes', 'A chronic condition affecting blood sugar levels'),
            ('Heart Disease', 'Conditions affecting the heart and blood vessels'),
            ('Hypertension', 'High blood pressure requiring ongoing management'),
            ('COVID-19', 'Viral respiratory illness requiring isolation and care'),
            ('Tuberculosis', 'Bacterial infection affecting the lungs'),
        ]:
            DiseaseInfo.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write(f'  ✓ {DiseaseInfo.objects.count()} disease info entries\n')

        # Gallery Images (placeholder titles — actual images should be uploaded via admin)
        gallery_data = [
            ('Hospital Main Entrance', 'building'),
            ('ICU Ward', 'ward'),
            ('Laboratory', 'facility'),
            ('Emergency Department', 'emergency'),
            ('Pediatric Ward', 'ward'),
            ('Surgery Theater', 'facility'),
            ('Radiology Suite', 'facility'),
            ('Pharmacy Counter', 'facility'),
        ]
        for title, cat in gallery_data:
            GalleryImage.objects.get_or_create(title=title, defaults={'category': cat})
        self.stdout.write(f'  ✓ {GalleryImage.objects.count()} gallery image placeholders\n')

        # ─── SAMPLE PATIENT DATA ────────────────────────────────────
        self.stdout.write('  Creating sample patient workflow data...\n')
        reg_user = User.objects.get(username='registration')
        doc_user = User.objects.get(username='doctor')
        cash_user = User.objects.get(username='cashier')
        lab_user = User.objects.get(username='laboratory')
        pharm_user = User.objects.get(username='pharmacy')
        ins_user = User.objects.get(username='insurance')

        sample_patients = [
            {'first_name': 'Rajesh', 'last_name': 'Thapa', 'age_value': 35, 'age_type': 'years',
             'gender': 'Male', 'phone': '+977-9841234501', 'email': 'rajesh@example.com',
             'address_line': 'Baneshwor, Kathmandu', 'province': 'Bagmati', 'district': 'Kathmandu',
             'municipality': 'Kathmandu Metropolitan', 'ward_number': '10', 'tole': 'Baneshwor',
             'blood_group': 'B+', 'allergies': 'None', 'chronic_conditions': 'Hypertension',
             'emergency_contact_name': 'Sita Thapa', 'emergency_contact_phone': '+977-9841234502',
             'emergency_contact_relation': 'Wife'},
            {'first_name': 'Sunita', 'last_name': 'Adhikari', 'age_value': 28, 'age_type': 'years',
             'gender': 'Female', 'phone': '+977-9841234503', 'email': 'sunita@example.com',
             'address_line': 'Pulchowk, Lalitpur', 'province': 'Bagmati', 'district': 'Lalitpur',
             'municipality': 'Lalitpur Metropolitan', 'ward_number': '3', 'tole': 'Pulchowk',
             'blood_group': 'O+', 'allergies': 'Penicillin', 'chronic_conditions': 'None',
             'emergency_contact_name': 'Bikash Adhikari', 'emergency_contact_phone': '+977-9841234504',
             'emergency_contact_relation': 'Father'},
            {'first_name': 'Hari', 'last_name': 'Prasad', 'age_value': 6, 'age_type': 'months',
             'gender': 'Male', 'phone': '+977-9841234505', 'email': '',
             'address_line': 'Bharatpur, Chitwan', 'province': 'Bagmati', 'district': 'Chitwan',
             'municipality': 'Bharatpur Metropolitan', 'ward_number': '5', 'tole': 'Main Road',
             'blood_group': 'A+', 'allergies': 'None', 'chronic_conditions': 'None',
             'emergency_contact_name': 'Maya Devi', 'emergency_contact_phone': '+977-9841234506',
             'emergency_contact_relation': 'Mother'},
            {'first_name': 'Anita', 'last_name': 'Kumari', 'age_value': 45, 'age_type': 'years',
             'gender': 'Female', 'phone': '+977-9841234507', 'email': 'anita@example.com',
             'address_line': 'Pokhara, Kaski', 'province': 'Gandaki', 'district': 'Kaski',
             'municipality': 'Pokhara Metropolitan', 'ward_number': '8', 'tole': 'Lakeside',
             'blood_group': 'AB+', 'allergies': 'Aspirin', 'chronic_conditions': 'Diabetes',
             'emergency_contact_name': 'Ramesh Kumar', 'emergency_contact_phone': '+977-9841234508',
             'emergency_contact_relation': 'Husband'},
            {'first_name': 'Dipak', 'last_name': 'Jha', 'age_value': 60, 'age_type': 'years',
             'gender': 'Male', 'phone': '+977-9841234509', 'email': 'dipak@example.com',
             'address_line': 'Janakpur, Dhanusha', 'province': 'Madhesh', 'district': 'Dhanusha',
             'municipality': 'Janakpur Municipality', 'ward_number': '2', 'tole': 'Temple Road',
             'blood_group': 'O-', 'allergies': 'None', 'chronic_conditions': 'Heart Disease, Diabetes',
             'emergency_contact_name': 'Kamala Jha', 'emergency_contact_phone': '+977-9841234510',
             'emergency_contact_relation': 'Wife'},
            {'first_name': 'Pramila', 'last_name': 'Rai', 'age_value': 3, 'age_type': 'weeks',
             'gender': 'Female', 'phone': '+977-9841234511', 'email': '',
             'address_line': 'Itahari, Sunsari', 'province': 'Koshi', 'district': 'Sunsari',
             'municipality': 'Itahari Municipality', 'ward_number': '4', 'tole': 'Hospital Road',
             'blood_group': 'B-', 'allergies': 'None', 'chronic_conditions': 'None',
             'emergency_contact_name': 'Krishna Rai', 'emergency_contact_phone': '+977-9841234512',
             'emergency_contact_relation': 'Father'},
            {'first_name': 'Bikash', 'last_name': 'Sharma', 'age_value': 42, 'age_type': 'years',
             'gender': 'Male', 'phone': '+977-9841234513', 'email': 'bikash@example.com',
             'address_line': 'Bhaktapur', 'province': 'Bagmati', 'district': 'Bhaktapur',
             'municipality': 'Bhaktapur Municipality', 'ward_number': '7', 'tole': 'Durbar Square',
             'blood_group': 'A-', 'allergies': 'Sulfa drugs', 'chronic_conditions': 'Asthma',
             'emergency_contact_name': 'Gita Sharma', 'emergency_contact_phone': '+977-9841234514',
             'emergency_contact_relation': 'Wife'},
            {'first_name': 'Maya', 'last_name': 'Gurung', 'age_value': 55, 'age_type': 'years',
             'gender': 'Female', 'phone': '+977-9841234515', 'email': 'maya@example.com',
             'address_line': 'Thamel, Kathmandu', 'province': 'Bagmati', 'district': 'Kathmandu',
             'municipality': 'Kathmandu Metropolitan', 'ward_number': '12', 'tole': 'Thamel',
             'blood_group': 'O+', 'allergies': 'None', 'chronic_conditions': 'Hypertension',
             'emergency_contact_name': 'Arun Gurung', 'emergency_contact_phone': '+977-9841234516',
             'emergency_contact_relation': 'Son'},
            {'first_name': 'Arun', 'last_name': 'Poudel', 'age_value': 18, 'age_type': 'years',
             'gender': 'Male', 'phone': '+977-9841234517', 'email': 'arun@example.com',
             'address_line': 'Hetauda, Makwanpur', 'province': 'Bagmati', 'district': 'Makwanpur',
             'municipality': 'Hetauda Municipality', 'ward_number': '1', 'tole': 'Industrial Area',
             'blood_group': 'AB-', 'allergies': 'None', 'chronic_conditions': 'None',
             'emergency_contact_name': 'Binita Poudel', 'emergency_contact_phone': '+977-9841234518',
             'emergency_contact_relation': 'Mother'},
            {'first_name': 'Gopal', 'last_name': 'Shrestha', 'age_value': 70, 'age_type': 'years',
             'gender': 'Male', 'phone': '+977-9841234519', 'email': 'gopal@example.com',
             'address_line': 'Patan, Lalitpur', 'province': 'Bagmati', 'district': 'Lalitpur',
             'municipality': 'Lalitpur Metropolitan', 'ward_number': '6', 'tole': 'Patan Durbar',
             'blood_group': 'B+', 'allergies': 'Ibuprofen', 'chronic_conditions': 'Heart Disease',
             'emergency_contact_name': 'Sunita Shrestha', 'emergency_contact_phone': '+977-9841234520',
             'emergency_contact_relation': 'Daughter'},
        ]

        patient_objs = []
        for pdata in sample_patients:
            prov = Province.objects.filter(name=pdata['province']).first()
            dist = District.objects.filter(name=pdata['district'], province=prov).first()
            # Clear old data first for re-runs
            Patient.objects.filter(phone=pdata['phone']).delete()
            p = Patient.objects.create(
                first_name=pdata['first_name'], last_name=pdata['last_name'],
                age_value=pdata['age_value'], age_type=pdata['age_type'],
                gender=pdata['gender'], phone=pdata['phone'], email=pdata['email'],
                address_line=pdata['address_line'],
                province=prov, district=dist,
                municipality=pdata['municipality'], ward_number=pdata['ward_number'],
                tole=pdata['tole'], blood_group=pdata['blood_group'],
                allergies=pdata['allergies'], chronic_conditions=pdata['chronic_conditions'],
                emergency_contact_name=pdata['emergency_contact_name'],
                emergency_contact_phone=pdata['emergency_contact_phone'],
                emergency_contact_relation=pdata['emergency_contact_relation'],
                registered_by=reg_user, registration_source='counter',
                is_new_patient=True,
            )
            patient_objs.append(p)
        self.stdout.write(f'  ✓ {len(patient_objs)} sample patients created\n')

        # OPD Visits for each patient — assign rotating doctors/departments
        today = timezone.now().date()
        visit_objs = []
        dept_list = list(dept_objs.values())
        for i, p in enumerate(patient_objs):
            doc = doc_objs[i % len(doc_objs)]
            dept = dept_list[i % len(dept_list)]
            fee = settings.REGISTRATION_FEE_NEW if p.is_new_patient else settings.REGISTRATION_FEE_OLD
            token = i + 1
            visit_status = 'waiting' if i < 3 else 'completed' if i < 7 else 'in_progress'
            v = OPDVisit.objects.create(
                patient=p, doctor=doc, department=dept,
                token_number=token, registration_fee=fee,
                payment_method='cash', visit_type='new',
                status=visit_status, created_by=reg_user,
            )
            visit_objs.append(v)
        self.stdout.write(f'  ✓ {len(visit_objs)} OPD visits created\n')

        # Patient Insurance — link patients 4, 5, 9 to insurers (with coverage)
        insurers = list(Insurer.objects.all())
        insurance_objs = []
        for i, p_idx in enumerate([3, 4, 8]):  # Anita, Dipak, Gopal
            if p_idx < len(patient_objs):
                ins = PatientInsurance.objects.create(
                    patient=patient_objs[p_idx],
                    insurer=insurers[i % len(insurers)],
                    policy_number=f'NHIF-{p_idx+1:06d}',
                    coverage_percentage=70.0 + (i * 5),
                )
                insurance_objs.append(ins)
        self.stdout.write(f'  ✓ {len(insurance_objs)} patient insurance records\n')

        # Bills — create bills for completed visits
        bill_objs = []
        opd_reg = HospitalService.objects.filter(code='OPD-001').first()
        for i, v in enumerate(visit_objs):
            if v.status in ('completed', 'in_progress'):
                p = v.patient
                # Clear old bill
                Bill.objects.filter(patient=p).delete()
                b = Bill.objects.create(
                    patient=p, total_amount=v.registration_fee,
                    discount_amount=0, net_amount=v.registration_fee,
                    payment_method='cash', discount_type='none', paid=True,
                    created_by=cash_user,
                )
                # Add bill item — OPD Registration
                if opd_reg:
                    BillItem.objects.create(
                        bill=b, service=opd_reg,
                        service_name=opd_reg.name, service_code=opd_reg.code,
                        service_price=opd_reg.price, quantity=1,
                        item_total=opd_reg.price,
                    )
                # Add extra services for some patients
                extra_services = [
                    HospitalService.objects.filter(code='LAB-001').first(),  # CBC
                    HospitalService.objects.filter(code='RAD-001').first(),  # X-Ray
                    HospitalService.objects.filter(code='RAD-004').first(),  # ECG
                ]
                if i % 2 == 0 and extra_services[0]:
                    svc = extra_services[0]
                    b.total_amount += svc.price
                    b.net_amount += svc.price
                    BillItem.objects.create(
                        bill=b, service=svc,
                        service_name=svc.name, service_code=svc.code,
                        service_price=svc.price, quantity=1, item_total=svc.price,
                    )
                if i % 3 == 0 and extra_services[1]:
                    svc = extra_services[1]
                    b.total_amount += svc.price
                    b.net_amount += svc.price
                    BillItem.objects.create(
                        bill=b, service=svc,
                        service_name=svc.name, service_code=svc.code,
                        service_price=svc.price, quantity=1, item_total=svc.price,
                    )
                b.save()  # Recalculate net_amount and trigger barcode
                bill_objs.append(b)
        self.stdout.write(f'  ✓ {len(bill_objs)} bills created\n')

        # Consultations — for completed visits (needed for Lab/Radiology requests)
        consult_objs = []
        med_list = list(Medicine.objects.all()[:4])
        for i, v in enumerate(visit_objs[:5]):
            if v.status == 'completed':
                Consultation.objects.filter(visit=v).delete()
                c = Consultation.objects.create(
                    visit=v, doctor=v.doctor,
                    diagnosis=f'Diagnosis: {["Tension headache","Viral fever","Angina","Muscle strain","Gastritis"][i]}',
                    clinical_notes=f'Prescribed medication and follow-up in 1 week.',
                )
                # Add prescriptions
                presc = Prescription.objects.create(
                    medicine_name=med_list[i % len(med_list)].name,
                    dosage=f'{["1 tablet twice daily","1 capsule daily","2 tablets daily","1 injection weekly","1 tablet thrice daily"][i]}',
                    frequency='daily',
                    duration='7 days',
                )
                c.prescriptions.add(presc)
                consult_objs.append(c)
        self.stdout.write(f'  ✓ {len(consult_objs)} consultations with prescriptions\n')

        # Lab Test Requests — for some patients (linked to consultations)
        lab_cats = list(LabCatalog.objects.all()[:5])
        lab_objs = []
        for i, p in enumerate(patient_objs[:6]):
            cat = lab_cats[i % len(lab_cats)]
            LabTestRequest.objects.filter(patient=p).delete()
            consult = consult_objs[i] if i < len(consult_objs) else None
            lr = LabTestRequest.objects.create(
                patient=p, consultation=consult,
                doctor=visit_objs[i].doctor if i < len(visit_objs) else doc_objs[0],
                test_name=cat.name,
                status='completed' if i < 4 else 'pending',
                result_notes=f'Normal range — all values within expected limits.' if i < 4 else '',
                clinical_note=f'Ordered as part of routine checkup.',
            )
            lab_objs.append(lr)
        self.stdout.write(f'  ✓ {len(lab_objs)} lab test requests\n')

        # Radiology Requests — for some patients (linked to consultations)
        rad_cats = list(RadiologyCatalog.objects.all()[:3])
        rad_objs = []
        for i, p in enumerate(patient_objs[:4]):
            cat = rad_cats[i % len(rad_cats)]
            RadiologyRequest.objects.filter(patient=p).delete()
            consult = consult_objs[i] if i < len(consult_objs) else None
            rr = RadiologyRequest.objects.create(
                patient=p, consultation=consult,
                doctor=visit_objs[i].doctor if i < len(visit_objs) else doc_objs[0],
                imaging_type=cat.imaging_type,
                clinical_note=f'Ordered for diagnostic evaluation.',
                status='completed' if i < 2 else 'requested',
                findings='No abnormality detected. All structures appear normal.' if i < 2 else '',
                impression='Normal study.' if i < 2 else '',
            )
            rad_objs.append(rr)
        self.stdout.write(f'  ✓ {len(rad_objs)} radiology requests\n')

        # Pharmacy Sales — for some patients (using SaleItem through model)
        pharm_objs = []
        for i, p in enumerate(patient_objs[:5]):
            med = med_list[i % len(med_list)]
            qty = 2 + i
            PharmacySale.objects.filter(patient=p).delete()
            ps = PharmacySale.objects.create(
                patient=p,
                total_amount=med.price * qty,
                discount=0, final_amount=med.price * qty,
                payment_method='cash',
                counter_staff=pharm_user,
            )
            SaleItem.objects.create(
                sale=ps, medicine=med,
                quantity=qty, price_at_sale=med.price,
                total=med.price * qty,
            )
            pharm_objs.append(ps)
        self.stdout.write(f'  ✓ {len(pharm_objs)} pharmacy sales\n')

        # Admissions — admit 2 patients
        beds = list(Bed.objects.filter(is_occupied=False)[:2])
        adm_objs = []
        for i, p_idx in enumerate([4, 7]):  # Dipak, Maya
            if p_idx < len(patient_objs) and i < len(beds):
                bed = beds[i]
                Admission.objects.filter(patient=patient_objs[p_idx]).delete()
                adm = Admission.objects.create(
                    patient=patient_objs[p_idx],
                    ward=bed.ward, bed=bed,
                    doctor=doc_objs[p_idx % len(doc_objs)],
                    admission_fee=2000,
                    status='admitted',
                    created_by=User.objects.get(username='admission'),
                )
                bed.is_occupied = True
                bed.save()
                adm_objs.append(adm)
        self.stdout.write(f'  ✓ {len(adm_objs)} admissions\n')

        # Insurance Claims — for insured patients
        claim_objs = []
        for i, ins in enumerate(insurance_objs):
            p = ins.patient
            # Find bill for this patient
            b = Bill.objects.filter(patient=p).first()
            if b:
                InsuranceClaim.objects.filter(patient=p).delete()
                coverage_amt = float(b.net_amount) * float(ins.coverage_percentage) / 100
                cl = InsuranceClaim.objects.create(
                    patient=p, insurance=ins,
                    amount=b.net_amount,
                    approved_amount=coverage_amt,
                    status='approved' if i < 2 else 'pending',
                    submitted_by=ins_user,
                )
                claim_objs.append(cl)
        self.stdout.write(f'  ✓ {len(claim_objs)} insurance claims\n')

        # Medical Records — auto-attached for all patients
        for p in patient_objs:
            MedicalRecord.objects.filter(patient=p).delete()
            MedicalRecord.objects.create(
                patient=p, department='registration',
                record_type='uploaded_pdf',
                title=f'OPD Registration - {p.patient_id}',
                summary=f'Patient {p.full_name} registered. Blood group: {p.blood_group}.',
                uploaded_by='system', staff_name='seed_all',
            )
        self.stdout.write(f'  ✓ {MedicalRecord.objects.count()} medical records\n')

        self.stdout.write(self.style.SUCCESS('\n✅ Hamro Hospital database seeded successfully!\n'))
        self.stdout.write('  Staff login: http://127.0.0.1:8000/accounts/login/\n')
        self.stdout.write('  Public site: http://127.0.0.1:8000/\n')
        self.stdout.write('  Password for all accounts: password123*#\n')
