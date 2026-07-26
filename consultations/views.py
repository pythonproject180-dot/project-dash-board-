from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Consultation, Prescription, LabTestRequest, RadiologyRequest
from patients.models import Patient, OPDVisit

@login_required
def consultation_create(request, visit_pk):
    visit = get_object_or_404(OPDVisit, pk=visit_pk)
    from laboratory.models import LabCatalog
    lab_catalog = LabCatalog.objects.filter(is_active=True)
    if request.method == 'POST':
        consultation = Consultation.objects.create(
            visit=visit,
            doctor=visit.doctor,
            diagnosis=request.POST.get('diagnosis'),
            clinical_notes=request.POST.get('clinical_notes'),
        )
        # Build prescriptions
        for i in range(int(request.POST.get('prescription_count', 0))):
            med = request.POST.get(f'medicine_{i}')
            if med:
                Prescription.objects.create(
                    medicine_name=med,
                    dosage=request.POST.get(f'dosage_{i}', ''),
                    frequency=request.POST.get(f'frequency_{i}', ''),
                    duration=request.POST.get(f'duration_{i}', ''),
                    instructions=request.POST.get(f'instructions_{i}', ''),
                )
        # Lab requests
        for test_name in request.POST.getlist('lab_tests'):
            LabTestRequest.objects.create(patient=visit.patient, consultation=consultation, doctor=visit.doctor, test_name=test_name)
        # Radiology requests
        for img_type in request.POST.getlist('radiology_types'):
            RadiologyRequest.objects.create(patient=visit.patient, consultation=consultation, doctor=visit.doctor, imaging_type=img_type)
        visit.status = 'completed'
        visit.save()
        return redirect('/doctors/dashboard/')
    return render(request, 'dashboard/consultation_form.html', {'visit': visit, 'lab_catalog': lab_catalog, 'role': 'doctor'})
