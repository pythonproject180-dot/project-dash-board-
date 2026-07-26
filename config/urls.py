from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Public website
    path('', include('website.urls')),
    # Auth & accounts
    path('accounts/', include('accounts.urls')),
    # All dashboard modules
    path('departments/', include('departments.urls')),
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('appointments/', include('appointments.urls')),
    path('consultation/', include('consultations.urls')),
    path('laboratory/', include('laboratory.urls')),
    path('radiology/', include('radiology.urls')),
    path('admissions/', include('admissions.urls')),
    path('billing/', include('billing.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('insurance/', include('insurance.urls')),
    path('reports/', include('reports.urls')),
    path('nursing/', include('nursing.urls')),
    path('operation-theatre/', include('operation_theatre.urls')),
    path('blood-bank/', include('blood_bank.urls')),
    path('medical-records/', include('medical_records.urls')),
    path('portal/', include('patient_portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
