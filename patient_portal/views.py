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
    """Patient portal signup — two modes:
    Mode 1: Existing patient — verify Hospital ID + phone, OTP verification, set password.
    Mode 2: New patient — online self-registration creates new Patient + Hospital ID
    from shared sequence, then OTP verification, set password.
    Both online and counter registration share the same patient numbering sequence.
    """
    if request.method == 'POST':
        step = request.POST.get('step', '1')
        signup_mode = request.POST.get('signup_mode', request.session.get('signup_mode', 'existing'))

        if step == '1':
            signup_mode = request.POST.get('signup_mode', 'existing')
            request.session['signup_mode'] = signup_mode

            if signup_mode == 'existing':
                # Mode 1: Existing patient — verify Hospital ID + phone
                hospital_id = request.POST.get('hospital_id')
                phone = request.POST.get('phone')
                patient = Patient.objects.filter(patient_id=hospital_id, phone=phone).first()
                if patient:
                    from .models import PortalUser
                    existing = PortalUser.objects.filter(patient=patient).first()
                    if existing:
                        return render(request, 'portal/signup.html', {
                            'error': 'Account already exists. Please login instead.', 'step': '1',
                            'signup_mode': 'existing',
                        })
                    otp = str(random.randint(100000, 999999))
                    request.session['portal_otp'] = otp
                    request.session['portal_patient_pk'] = patient.pk
                    request.session['portal_phone'] = phone
                    return render(request, 'portal/signup.html', {
                        'step': '2', 'phone': phone, 'otp_hint': f'Demo OTP: {otp}',
                        'hospital_id': hospital_id, 'patient_name': patient.full_name,
                        'signup_mode': 'existing',
                    })
                else:
                    return render(request, 'portal/signup.html', {
                        'error': 'Patient not found. Please verify your Hospital ID and phone number, or register as a new patient.',
                        'step': '1', 'signup_mode': 'existing',
                    })

            else:
                # Mode 2: New patient — online self-registration
                first_name = request.POST.get('first_name', '')
                last_name = request.POST.get('last_name', '')
                gender = request.POST.get('gender', '')
                phone = request.POST.get('phone', '')
                email = request.POST.get('email', '')
                age_value = request.POST.get('age_value', '0')
                age_type = request.POST.get('age_type', 'years')
                address_line = request.POST.get('address_line', '')
                municipality = request.POST.get('municipality', '')
                emergency_contact_name = request.POST.get('emergency_contact_name', '')
                emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
                emergency_contact_relation = request.POST.get('emergency_contact_relation', '')
                blood_group = request.POST.get('blood_group', '')

                # Validate required fields
                if not first_name or not last_name or not gender or not phone:
                    return render(request, 'portal/signup.html', {
                        'error': 'Please fill in all required fields (First Name, Last Name, Gender, Phone).',
                        'step': '1', 'signup_mode': 'new',
                        'form_data': request.POST.dict(),
                    })

                # Check if phone already registered as patient
                existing_patient = Patient.objects.filter(phone=phone).first()
                if existing_patient:
                    # Phone already exists — redirect to existing patient mode
                    from .models import PortalUser
                    existing_portal = PortalUser.objects.filter(patient=existing_patient).first()
                    if existing_portal:
                        return render(request, 'portal/signup.html', {
                            'error': f'A patient with this phone number already exists (ID: {existing_patient.patient_id}). Please login or use "Existing Patient" mode.',
                            'step': '1', 'signup_mode': 'new',
                            'form_data': request.POST.dict(),
                        })
                    # Patient exists but no portal account — offer to link
                    otp = str(random.randint(100000, 999999))
                    request.session['portal_otp'] = otp
                    request.session['portal_patient_pk'] = existing_patient.pk
                    request.session['portal_phone'] = phone
                    request.session['signup_mode'] = 'existing'
                    return render(request, 'portal/signup.html', {
                        'step': '2', 'phone': phone, 'otp_hint': f'Demo OTP: {otp}',
                        'hospital_id': existing_patient.patient_id,
                        'patient_name': existing_patient.full_name,
                        'signup_mode': 'existing',
                        'info': f'Your phone is already registered as {existing_patient.patient_id}. Creating portal account for this patient.',
                    })

                # Create new patient with Hospital ID from shared sequence
                from accounts.models import Province, District
                province = Province.objects.filter(name='Bagmati').first()
                district = District.objects.filter(name='Kathmandu', province=province).first()

                new_patient = Patient.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    phone=phone,
                    email=email,
                    age_value=int(age_value) if age_value else 0,
                    age_type=age_type,
                    address_line=address_line,
                    municipality=municipality,
                    province=province,
                    district=district,
                    emergency_contact_name=emergency_contact_name,
                    emergency_contact_phone=emergency_contact_phone,
                    emergency_contact_relation=emergency_contact_relation,
                    blood_group=blood_group,
                    registration_source='online',
                    is_new_patient=True,
                )

                # Auto-attach medical record
                MedicalRecord.objects.create(
                    patient=new_patient, department='registration',
                    record_type='uploaded_pdf',
                    title=f'Online Registration - {new_patient.patient_id}',
                    summary=f'Patient registered online. ID: {new_patient.patient_id}',
                    uploaded_by='portal_signup', staff_name='Online Registration',
                )

                # Generate OTP for phone verification
                otp = str(random.randint(100000, 999999))
                request.session['portal_otp'] = otp
                request.session['portal_patient_pk'] = new_patient.pk
                request.session['portal_phone'] = phone
                request.session['signup_mode'] = 'new'

                return render(request, 'portal/signup.html', {
                    'step': '2', 'phone': phone, 'otp_hint': f'Demo OTP: {otp}',
                    'hospital_id': new_patient.patient_id,
                    'patient_name': new_patient.full_name,
                    'signup_mode': 'new',
                    'info': f'Registration successful! Your Hospital ID is {new_patient.patient_id}. Please verify your phone to complete signup.',
                })

        elif step == '2':
            # Step 2: OTP verification (same for both modes)
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('portal_otp')
            patient_pk = request.session.get('portal_patient_pk')

            if entered_otp == stored_otp and patient_pk:
                patient = Patient.objects.get(pk=patient_pk)
                signup_mode = request.session.get('signup_mode', 'existing')
                return render(request, 'portal/signup.html', {
                    'step': '3', 'patient_pk': patient_pk,
                    'patient_name': patient.full_name,
                    'hospital_id': patient.patient_id,
                    'signup_mode': signup_mode,
                })
            else:
                signup_mode = request.session.get('signup_mode', 'existing')
                return render(request, 'portal/signup.html', {
                    'error': 'Invalid OTP. Please try again.',
                    'step': '2', 'phone': request.session.get('portal_phone'),
                    'otp_hint': f'Demo OTP: {stored_otp}',
                    'signup_mode': signup_mode,
                })

        elif step == '3':
            # Step 3: Set password and create account (same for both modes)
            patient_pk = request.POST.get('patient_pk')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                signup_mode = request.session.get('signup_mode', 'existing')
                return render(request, 'portal/signup.html', {
                    'error': 'Passwords do not match.',
                    'step': '3', 'patient_pk': patient_pk,
                    'signup_mode': signup_mode,
                })

            patient = Patient.objects.get(pk=patient_pk)
            from .models import PortalUser
            PortalUser.objects.create(
                patient=patient,
                username=patient.patient_id,
                password_hash=password,
                phone=patient.phone,
            )
            request.session.pop('portal_otp', None)
            request.session.pop('signup_mode', None)
            request.session['portal_patient_id'] = patient.pk
            return redirect('/portal/dashboard/')

    # Default — show mode choice
    signup_mode = request.GET.get('mode', request.session.get('signup_mode', ''))
    context = {'step': '1'}
    if signup_mode == 'new':
        context['signup_mode'] = 'new'
    else:
        context['signup_mode'] = 'existing'
    return render(request, 'portal/signup.html', context)


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
