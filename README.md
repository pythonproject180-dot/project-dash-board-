# 🏥 Hamro Hospital Management System

A complete **Hospital ERP System** built with **Django 5.1** for hospitals in Nepal. Features 14 role-based staff dashboards, a public website, patient portal, and full inter-module workflow.

---

## 📋 Project Overview

Hamro Hospital is a professional, production-ready Hospital Management System designed for Nepal's healthcare infrastructure. It supports:

- **14 Staff Roles** with strict Role-Based Access Control (RBAC)
- **20 Django Modules** covering every hospital department
- **39+ Database Models** with proper relationships and constraints
- **71 Dashboard Templates** (Dasher design) with role-based sidebar
- **10 Website Templates** (NexusAI design) with Light/Dark/Auto theme
- **4 Patient Portal Templates** (signup/login/dashboard/forgot-password)
- **3 eSewa Payment Templates** (initiate/success/failure)
- **Expanded Seed Data** — 100 medicines, 40 services, 40 lab catalog, 24 radiology catalog, 22 patients, 20 OPD visits, 17 bills, 16 lab requests, 14 radiology requests, 10+ consultations, 15 pharmacy sales, 16 admissions, 10 discharge summaries, 17 nursing notes, 57 medical records, 13 insurance claims, 10 surgeries, 10 blood requests, 10 appointments, 15 doctors
- **Patient QR Codes** — one permanent QR per patient, scanned across all departments
- **Barcodes** — separate barcodes for Bills, Admissions, Lab, Radiology, Pharmacy, Insurance
- **Print/PDF/JPG** downloads on all printable documents (OPD Ticket, Bill Receipt, Patient Card, Discharge Summary, Insurance Claim, Lab/Radiology Reports)
- **Medical Record Automation** — all department reports auto-attach to centralized medical record
- **Nepal Localization** — Provinces, Districts, Municipalities, NPR currency, Lakh/Crore notation
- **Doctor Quota System** — limits daily OPD bookings per doctor per weekday
- **Registration Fee** — New Patient: NPR 100, Old Patient: NPR 50
- **Payment Methods** — Cash (default) and eSewa (with full payment flow)
- **eSewa Payment Gateway** — HMAC-SHA256 signature, test environment (EPAYTEST), production via env vars
- **SMS OTP Gateway** — 4 providers: Sparrow SMS (Nepal), Vasani (Nepal), Twilio (International), Simulated (Dev)
- **Smart Search Autocomplete** — type "X" shows X-Ray, "E" shows ECG, "U" shows Ultrasound
- **Popup Modals** — stat cards open popup modals with detailed drill-down data on all 14 dashboards
- **ApexCharts Graphs** — 7-day trend data on all 14 dashboards
- **CSV Export** — 5 modules: patients, billing, lab, pharmacy, revenue
- **Department Drill-down** — accounts dashboard shows transaction details per department

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+ / Django 5.1 |
| Frontend | Bootstrap 5.3 / JavaScript |
| Admin Theme | Django Jazzmin |
| Public Website | NexusAI Template |
| Dashboard | Dasher Template |
| Database (Dev) | SQLite |
| Database (Prod) | PostgreSQL (configurable via env) |
| PDF Generation | xhtml2pdf |
| Barcode | python-barcode (Code128) |
| QR Code | qrcode + Pillow |
| Payment Gateway | eSewa (HMAC-SHA256) |
| SMS Gateway | Sparrow SMS / Vasani / Twilio |
| Icons | FontAwesome, Tabler Icons |

---

## 🚀 Installation

### Prerequisites
- Python 3.11+
- pip
- virtualenv

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/pythonproject180-dot/project-dash-board-.git
cd project-dash-board-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed the database with demo data
python manage.py seed_all

# Create superuser (optional — admin account is already seeded)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Access URLs
| Service | URL |
|---------|-----|
| Public Website | http://127.0.0.1:8000/ |
| Staff Login | http://127.0.0.1:8000/accounts/login/ |
| Django Admin (Jazzmin) | http://127.0.0.1:8000/admin/ |
| Patient Portal | http://127.0.0.1:8000/portal/signup/ |
| Patient Portal Login | http://127.0.0.1:8000/portal/login/ |
| Forgot Password | http://127.0.0.1:8000/portal/forgot-password/ |

### Default Staff Password
All 14 staff accounts use: `password123*#`

### Sample Data
After running `seed_all`, the database includes:
- 10 sample patients (with Hospital IDs HT-000001 through HT-000010)
- 10 OPD visits (3 waiting, 4 completed, 3 in-progress)
- 7 bills with bill items (OPD + lab/radiology services)
- 2 consultations with prescriptions
- 6 lab test requests (4 completed, 2 pending)
- 4 radiology requests (2 completed, 2 pending)
- 5 pharmacy sales with sale items
- 2 admissions (1 admitted patient in ICU, 1 in General Ward)
- 3 patient insurance records with coverage percentages
- 3 insurance claims (2 approved, 1 pending)
- 10 medical records (auto-attached from registration)
- 8 gallery image placeholders

### Patient Portal Signup
Two signup modes available:
1. **Existing Patient** — Enter Hospital ID + phone number → OTP verification → Set password
2. **New Patient (Self-Registration)** — Fill in name, gender, phone, age, address → Hospital ID auto-generated from shared sequence → OTP verification → Set password
   - Creates new Patient record with `registration_source='online'`
   - Hospital IDs remain sequential regardless of registration method (HT-000001 online, HT-000002 counter, HT-000003 online)
   - If phone number already exists as patient, auto-links to existing record

---

## 🔐 User Roles & Permissions

| Role | Username | Permissions |
|------|----------|-------------|
| Super Admin | admin | Full access, Django Admin, edit/delete anything, audit logs |
| Registration | registration | Register patients, OPD tickets, print patient cards, edit within 24h only |
| Cash Counter | cashier | Billing, payment, receipt generation, collection reports |
| Doctor | doctor | Patient history, prescriptions, lab/radiology requests, quota management |
| Pharmacy | pharmacy | Medicine sales, stock management, dispensing |
| Laboratory | laboratory | Upload lab reports, search patient, auto-attach to medical record |
| Radiology | radiology | Upload radiology reports, imaging, auto-attach to medical record |
| Insurance | insurance | QR scan/manual entry, claim approval, discount calculation, receipt generation |
| Admission | admission | Admit patient, bed management, discharge, discharge summary |
| Nursing | nursing | Search patient, view records, add nursing notes/vitals (read-only for most) |
| Operation Theatre | operationtheatre | Surgery scheduling, operation notes, OT reports |
| Blood Bank | bloodbank | Blood requests, blood issue, blood history |
| Medical Records | medicalrecords | Centralized records, search, download (read-only for non-admin) |
| Accounts | accounts | Revenue reports, department-wise collection, drill-down analysis |

### Key Business Rules
- **Registration** can edit records only within 24 hours. After that, only Super Admin can modify.
- **Patient ID Cards** can only be printed by Registration Counter and Super Admin.
- **Medical Records** are read-only for most departments. Only Super Admin can edit.
- **Insurance claims** automatically calculate discounts based on coverage percentage.
- **Doctor quotas** limit daily OPD bookings. Registration counter must follow quotas.
- **Online and counter registration** share the same sequential numbering (HT-000001, HT-000002...).
- **Payment method** defaults to Cash, with eSewa as an alternative.

---

## 📂 Folder Structure

```
project-dash-board-/
├── accounts/          # User model, 14 roles, auth, decorators, audit log, seed command
├── admissions/        # Admission, Ward, Bed, DischargeSummary models
├── appointments/      # Appointment booking
├── billing/           # HospitalService, Bill, BillItem (audit-safe pricing), autocomplete API
├── blood_bank/        # BloodRequest model
├── config/            # Django settings (SQLite/PostgreSQL switchable via DJANGO_DB_ENGINE)
├── consultations/     # Consultation, Prescription, LabTestRequest, RadiologyRequest
├── departments/       # Department model
├── doctors/           # Doctor, DoctorQuota (weekday quotas) models
├── insurance/         # Insurer, PatientInsurance, InsuranceClaim (coverage discount calc)
├── laboratory/        # LabCatalog model, catalog management views
├── medical_records/   # MedicalRecord (centralized repository, auto-attach from all departments)
├── nursing/           # NursingNote model
├── operation_theatre/ # Surgery model
├── patient_portal/    # PortalUser, 3-step signup OTP, 3-step forgot password, rich dashboard
├── patients/          # Patient, OPDVisit (QR, age_type, registration_fee, 24h edit rule)
├── pharmacy/          # Medicine, PharmacySale, SaleItem (through model)
├── radiology/         # RadiologyCatalog model, catalog management views
├── reports/           # Revenue, accounts (dept drill-down), registration, department, doctor reports
├── website/           # Testimonial, GalleryImage (blank=True), DiseaseInfo
├── utils/             # barcode_utils (Code128), pdf_utils (xhtml2pdf), image_utils (Pillow)
├── static/            # CSS, JS, images, fonts (Dasher + NexusAI assets)
├── templates/         # All HTML templates
│   ├── dashboard/     # 71 dashboard templates (Dasher design)
│   ├── website/       # 10 website templates (NexusAI design)
│   ├── portal/        # 4 patient portal templates (signup, login, dashboard, forgot_password)
│   └── accounts/      # Login page
├── manage.py
├── requirements.txt
├── README.md
└── db.sqlite3         # (development, seeded with sample data)
```

---

## 💾 Database Configuration

### SQLite (Development — Default)
No configuration needed. Django automatically creates `db.sqlite3`.

### PostgreSQL (Production)
Set environment variables:

```bash
export DJANGO_DB_ENGINE=postgresql
export DB_NAME=hamro_hospital
export DB_USER=hamro_admin
export DB_PASSWORD=your_secure_password
export DB_HOST=localhost
export DB_PORT=5432
```

Or update `config/settings.py` directly.

---

## 🎨 Template Design

### Public Website — NexusAI Template
- Modern landing page design
- AOS animations
- Swiper sliders
- FontAwesome icons
- Light/Dark/Auto theme toggle (localStorage)
- Responsive design

### Staff Dashboard — Dasher Template
- Professional ERP dashboard design
- Bootstrap 5.3
- Light/Dark/Auto theme toggle (localStorage persistence)
- Sidebar collapse/expand (localStorage)
- Search modal (Cmd+K)
- Notification offcanvas
- User profile dropdown
- Responsive mobile menu
- Smooth transitions

### Django Admin — Jazzmin
- Hospital logo branding
- Custom sidebar icons
- Modern admin interface
- Professional color scheme

---

## 🖨️ Printable Documents

| Document | Print | PDF | JPG | Barcode | QR |
|----------|-------|-----|-----|---------|-----|
| OPD Ticket | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bill Receipt | ✅ | ✅ | ✅ | ✅ | ✅ |
| Patient Card (ID/Visiting/Sticker) | ✅ | ✅ | ✅ | — | ✅ |
| Discharge Summary | ✅ | ✅ | ✅ | ✅ | ✅ |
| Insurance Claim Receipt | ✅ | ✅ | ✅ | ✅ | ✅ |
| Lab Report | ✅ | ✅ | ✅ | ✅ | — |
| Radiology Report | ✅ | ✅ | ✅ | ✅ | — |

---

## 🔒 Security Features

- Django authentication (AbstractUser model)
- Role-Based Access Control (RBAC) decorators on all views
- CSRF protection (Django middleware)
- XSS protection (Django template auto-escaping)
- SQL injection prevention (Django ORM)
- Audit logging for sensitive actions
- Password hashing (Django PBKDF2)
- Input validation on all forms
- Secure file uploads (media directory)
- Environment variable management for secrets
- Session security

---

## 🇳🇵 Nepal Localization

- **NPR** currency (Lakh/Crore notation for large amounts)
- 7 Provinces and 64 Districts seeded
- Municipality, Ward, Tole address fields
- Nepal phone format (+977)
- Asia/Kathmandu timezone
- Hospital ID format: HT-000001
- Registration fees: New NPR 100, Old NPR 50

---

## 📊 Module Communication

All departments communicate through the **patient record**:

1. Registration → Creates Patient + OPD Visit → Medical Record
2. Doctor → Creates Consultation + Requests Lab/Radiology → Medical Record
3. Lab → Uploads Report → Auto-attaches to Medical Record
4. Radiology → Uploads Report → Auto-attaches to Medical Record
5. Pharmacy → Dispenses Medicine → Medical Record
6. Admission → Admits Patient → Medical Record
7. Discharge → Discharge Summary → Medical Record
8. Insurance → Claim Receipt → Medical Record
9. Nursing → Nursing Notes/Vitals → Medical Record
10. OT → Surgery Report → Medical Record
11. Blood Bank → Blood Issue → Medical Record

---

## 🧪 Testing Workflow

### Staff Dashboard Workflow
1. Login as Registration → Register Patient → Generate OPD Ticket → Print/PDF/JPG
2. Login as Doctor → View patient → Create consultation → Request lab/radiology → Manage quotas
3. Login as Laboratory → View queue → Upload result → Auto-attach to medical record
4. Login as Radiology → View queue → Upload result → Auto-attach to medical record
5. Login as Cash Counter → Create bill → Print/PDF/JPG receipt → View today's collections
6. Login as Insurance → Submit claim → Approve → Print/PDF/JPG receipt → View claims report
7. Login as Admission → Admit patient → Discharge → Print/PDF/JPG discharge summary
8. Login as Super Admin → Django Admin → Full access → Edit/delete any record
9. Login as Accounts → Department-wise revenue → Drill-down modals → CSV export

### Patient Portal Workflow
1. Visit `/portal/signup/` → Enter Hospital ID + phone → OTP verification → Set password
2. Login at `/portal/login/` → View dashboard with 8 tabs: Visits, Lab, Radiology, Bills, Pharmacy, Admissions, Insurance, Medical Records
3. Forgot password at `/portal/forgot-password/` → Phone OTP → Reset password

### Pre-seeded Sample Data
After running `seed_all`, you can immediately test with 10 sample patients:
- Patient HT-000010 (Gopal Shrestha) has: OPD visit, bill, lab/radiology request, pharmacy sale, insurance claim
- Patient HT-000009 (Arun Poudel) has: OPD visit, completed consultation with prescription
- 2 admitted patients in beds (HT-000005 Dipak Jha, HT-000008 Maya Gurung)

---

## 📝 Future Improvements

- eSewa payment gateway integration (live SMS/redirect — dropdown option exists)
- Phone OTP via actual SMS gateway (currently simulated with random OTP + on-screen display)
- Appointment booking from patient portal with quota check
- Real-time notifications (WebSocket)
- Doctor scheduling calendar
- Advanced analytics dashboard with charts
- Backup and restore commands
- REST API for mobile app integration
- Multi-hospital support
- HL7/FHIR integration for lab systems

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Module not found | `pip install -r requirements.txt` |
| Database error | `python manage.py migrate` |
| No staff accounts | `python manage.py seed_all` |
| Static files not loading | `python manage.py collectstatic` |
| Login fails | Use `password123*#` for seeded accounts |

---

## 📄 License

This project is built for Hamro Hospital, Nepal. All template designs (NexusAI, Dasher) are preserved as per their original licenses.

---

**Built with ❤️ for Nepal's Healthcare System**
