"""
Django settings for Hamro Hospital Management System.
Supports both SQLite (development) and PostgreSQL (production).
Switch using DJANGO_DB_ENGINE environment variable.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-hamro-hospital-dev-key-change-in-production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Hamro Hospital apps
    'accounts',
    'website',
    'departments',
    'doctors',
    'patients',
    'appointments',
    'consultations',
    'laboratory',
    'radiology',
    'admissions',
    'billing',
    'pharmacy',
    'insurance',
    'reports',
    'patient_portal',
    'medical_records',
    'nursing',
    'operation_theatre',
    'blood_bank',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.role_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration — switchable via DJANGO_DB_ENGINE environment variable
# Default: SQLite for development
# Set DJANGO_DB_ENGINE=postgresql for production
DJANGO_DB_ENGINE = os.environ.get('DJANGO_DB_ENGINE', 'sqlite')

if DJANGO_DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'hamro_hospital'),
            'USER': os.environ.get('DB_USER', 'hamro_admin'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'change_me_in_production'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/login-success/'

# Jazzmin Django Admin Configuration
JAZZMIN_SETTINGS = {
    "title": "Hamro Hospital Admin",
    "site_header": "Hamro Hospital",
    "site_brand": "Hamro Hospital",
    "site_logo": "/static/images/brand/logo/hamro-hospital-logo.jpg",
    "login_logo": "/static/images/brand/logo/hamro-login-logo.png",
    "login_logo_dark": "/static/images/brand/logo/hamro-login-logo.png",
    "site_icon": "/static/images/brand/logo/logo-icon.svg",
    "welcome_sign": "Welcome to Hamro Hospital Admin",
    "search_model": ["accounts.User", "patients.Patient"],
    "user_avatar": None,
    "show_ui_builder": False,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "auth.User": "fas fa-user",
        "accounts.User": "fas fa-user-shield",
        "accounts.AuditLog": "fas fa-clipboard-list",
        "patients.Patient": "fas fa-hospital-user",
        "patients.OPDVisit": "fas fa-ticket",
        "billing.Bill": "fas fa-file-invoice-dollar",
        "billing.HospitalService": "fas fa-hand-holding-usd",
        "admissions.Admission": "fas fa-bed",
        "admissions.Ward": "fas fa-procedures",
        "admissions.Bed": "fas fa-bed-pulse",
        "pharmacy.Medicine": "fas fa-pills",
        "pharmacy.PharmacySale": "fas fa-prescription-bottle-alt",
        "laboratory.LabCatalog": "fas fa-flask",
        "radiology.RadiologyCatalog": "fas fa-x-ray",
        "consultations.Consultation": "fas fa-stethoscope",
        "consultations.LabTestRequest": "fas fa-vials",
        "consultations.RadiologyRequest": "fas fa-x-ray",
        "insurance.Insurer": "fas fa-shield-alt",
        "insurance.PatientInsurance": "fas fa-id-card-alt",
        "insurance.InsuranceClaim": "fas fa-file-contract",
        "departments.Department": "fas fa-hospital",
        "doctors.Doctor": "fas fa-user-md",
        "appointments.Appointment": "fas fa-calendar-check",
        "blood_bank.BloodStock": "fas fa-tint",
        "nursing.NursingNote": "fas fa-notes-medical",
        "operation_theatre.Surgery": "fas fa-procedures",
        "medical_records.MedicalRecord": "fas fa-file-medical",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "order_with_respect_to": [
        "accounts", "patients", "billing", "admissions", "consultations",
        "pharmacy", "laboratory", "radiology", "insurance", "departments",
        "doctors", "appointments", "nursing", "operation_theatre", "blood_bank",
        "medical_records", "auth",
    ],
    "topmenu_links": [
        {"name": "Dashboard", "url": "/accounts/dashboard/super-admin/", "new_window": False},
        {"name": "Public Website", "url": "/", "new_window": True},
    ],
    "sidebar_link": "/accounts/dashboard/super-admin/",
}

JAZZMIN_UI_TEMPLATES = {
    "login": "jazzmin/login.html",
    "change_form": "jazzmin/change_form.html",
    "change_list": "jazzmin/change_list.html",
}

# eSewa configuration
ESEWA_MERCHANT_CODE = os.environ.get('ESEWA_MERCHANT_CODE', 'EPAYTEST')
ESEWA_MERCHANT_SECRET = os.environ.get('ESEWA_MERCHANT_SECRET', '8gBm;6&z')

# Registration fees
REGISTRATION_FEE_NEW = 100  # NPR for new patient
REGISTRATION_FEE_OLD = 50   # NPR for returning patient

# Nepal currency formatting helper
def format_npr(amount):
    """Format NPR amounts in lakh/crore notation for display."""
    try:
        amt = float(amount)
        if amt >= 10000000:  # 1 crore
            return f"{amt/10000000:.2f} Crore"
        elif amt >= 100000:  # 1 lakh
            return f"{amt/100000:.2f} Lakh"
        else:
            return f"NPR {amt:,.0f}"
    except (ValueError, TypeError):
        return f"NPR {amount}"

# Audit logging settings
AUDIT_LOG_ENABLED = True
