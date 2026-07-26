from django.shortcuts import render, redirect, get_object_or_404
from patients.models import Patient
from billing.models import Bill
from consultations.models import LabTestRequest, RadiologyRequest
from pharmacy.models import PharmacySale
from insurance.models import InsuranceClaim
from admissions.models import Admission
from medical_records.models import MedicalRecord
from django.utils import timezone
import random


def portal_signup(request):
    """Patient portal signup — Hospital ID + phone verification (simulated OTP).
    Patient must already be registered at the hospital counter.
    Online registration and counter registration share the same patient numbering sequence.
    """
    if request.method == 'POST':
        step = request.POST.get('step', '1')

        if step == '1':
            # Step 1: Verify Hospital ID and phone
            hospital_id = request.POST.get('hospital_id')
            phone = request.POST.get('phone')
            patient = Patient.objects.filter(patient_id=hospital_id, phone=phone).first()
            if patient:
                from .models import PortalUser
                existing = PortalUser.objects.filter(patient=patient).first()
                if existing:
                    return render(request, 'portal/signup.html', {'error': 'Account already exists. Please login instead.', 'step': '1'})
                # Generate OTP (simulated — in production, send via SMS)
                otp = str(random.randint(100000, 999999))
                request.session['portal_otp'] = otp
                request.session['portal_patient_pk'] = patient.pk
                request.session['portal_phone'] = phone
                return render(request, 'portal/signup.html', {
                    'step': '2', 'phone': phone, 'otp_hint': f'Demo OTP: {otp}',
                    'hospital_id': hospital_id, 'patient_name': patient.full_name,
                })
            else:
                return render(request, 'portal/signup.html', {
                    'error': 'Patient not found. Please verify your Hospital ID and phone number.',
                    'step': '1',
                })

        elif step == '2':
            # Step 2: OTP verification
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('portal_otp')
            patient_pk = request.session.get('portal_patient_pk')

            if entered_otp == stored_otp and patient_pk:
                patient = Patient.objects.get(pk=patient_pk)
                # Step 3: Set password
                return render(request, 'portal/signup.html', {
                    'step': '3', 'patient_pk': patient_pk,
                    'patient_name': patient.full_name,
                    'hospital_id': patient.patient_id,
                })
            else:
                return render(request, 'portal/signup.html', {
                    'error': 'Invalid OTP. Please try again.',
                    'step': '2', 'phone': request.session.get('portal_phone'),
                    'otp_hint': f'Demo OTP: {stored_otp}',
                })

        elif step == '3':
            # Step 3: Set password and create account
            patient_pk = request.POST.get('patient_pk')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                return render(request, 'portal/signup.html', {
                    'error': 'Passwords do not match.',
                    'step': '3', 'patient_pk': patient_pk,
                })

            patient = Patient.objects.get(pk=patient_pk)
            from .models import PortalUser
            PortalUser.objects.create(
                patient=patient,
                username=patient.patient_id,
                password_hash=password,
                phone=patient.phone,
            )
            # Clear session OTP
            request.session.pop('portal_otp', None)
            request.session['portal_patient_id'] = patient.pk
            return redirect('/portal/dashboard/')

    return render(request, 'portal/signup.html', {'step': '1'})


def portal_login(request):
    """Patient portal login — by Hospital ID or phone number + password."""
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        password = request.POST.get('password')
        from .models import PortalUser
        portal = PortalUser.objects.filter(username=hospital_id, password_hash=password).first()
        if not portal:
            # Also try matching by phone number
            portal = PortalUser.objects.filter(phone=hospital_id, password_hash=password).first()
        if portal and portal.is_active:
            portal.last_login = timezone.now()
            portal.save()
            request.session['portal_patient_id'] = portal.patient.pk
            return redirect('/portal/dashboard/')
        return render(request, 'portal/login.html', {'error': 'Invalid credentials. Try your Hospital ID or phone number.'})
    return render(request, 'portal/login.html')


def portal_forgot_password(request):
    """Forgot password — recovery through phone number (OTP) only.
    As per PDF: "Forgot Password — Recovery only through phone number (OTP)."
    """
    if request.method == 'POST':
        step = request.POST.get('step', '1')

        if step == '1':
            phone = request.POST.get('phone')
            from .models import PortalUser
            portal = PortalUser.objects.filter(phone=phone).first()
            if portal:
                otp = str(random.randint(100000, 999999))
                request.session['forgot_otp'] = otp
                request.session['forgot_portal_pk'] = portal.pk
                return render(request, 'portal/forgot_password.html', {
                    'step': '2', 'phone': phone,
                    'otp_hint': f'Demo OTP: {otp}',
                })
            else:
                return render(request, 'portal/forgot_password.html', {
                    'error': 'No account found with this phone number.',
                    'step': '1',
                })

        elif step == '2':
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('forgot_otp')
            portal_pk = request.session.get('forgot_portal_pk')

            if entered_otp == stored_otp and portal_pk:
                return render(request, 'portal/forgot_password.html', {
                    'step': '3', 'portal_pk': portal_pk,
                })
            else:
                return render(request, 'portal/forgot_password.html', {
                    'error': 'Invalid OTP.',
                    'step': '2',
                    'otp_hint': f'Demo OTP: {stored_otp}',
                })

        elif step == '3':
            portal_pk = request.POST.get('portal_pk')
            new_password = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')

            if new_password != confirm:
                return render(request, 'portal/forgot_password.html', {
                    'error': 'Passwords do not match.',
                    'step': '3', 'portal_pk': portal_pk,
                })

            from .models import PortalUser
            portal = PortalUser.objects.get(pk=portal_pk)
            portal.password_hash = new_password
            portal.save()
            request.session.pop('forgot_otp', None)
            return redirect('/portal/login/')

    return render(request, 'portal/forgot_password.html', {'step': '1'})


def portal_dashboard(request):
    """Patient Dashboard — view medical records, lab reports, radiology, insurance,
    prescriptions, visit history, appointments, downloads.
    Cannot print Patient ID Card. Only Registration and Super Admin can print.
    """
    pid = request.session.get('portal_patient_id')
    if not pid:
        return redirect('/portal/login/')
    patient = get_object_or_404(Patient, pk=pid)
    visits = patient.opd_visits.all()
    lab_results = LabTestRequest.objects.filter(patient=patient).order_by('-created_at')
    rad_results = RadiologyRequest.objects.filter(patient=patient).order_by('-created_at')
    bills = Bill.objects.filter(patient=patient).order_by('-created_at')
    pharmacy = PharmacySale.objects.filter(patient=patient).order_by('-sale_date')
    admissions = Admission.objects.filter(patient=patient).order_by('-admission_date')
    claims = InsuranceClaim.objects.filter(patient=patient).order_by('-created_at')
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-created_at')[:20]

    # Patient cannot print Patient ID Card
    can_print_card = False

    context = {
        'patient': patient, 'visits': visits, 'lab_results': lab_results,
        'rad_results': rad_results, 'bills': bills, 'pharmacy': pharmacy,
        'admissions': admissions, 'claims': claims,
        'medical_records': medical_records,
        'can_print_card': can_print_card,
    }
    return render(request, 'portal/dashboard.html', context)


def portal_logout(request):
    request.session.pop('portal_patient_id', None)
    return redirect('/portal/login/')
