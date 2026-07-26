from django.urls import path
from . import views

urlpatterns = [
    path('revenue/', views.revenue_dashboard, name='revenue_dashboard'),
    path('accounts/', views.accounts_dashboard, name='accounts_dashboard'),
    path('registration/', views.registration_report, name='registration_report'),
    path('department/', views.department_report, name='department_report'),
    path('doctor/', views.doctor_report, name='doctor_report'),
    path('pharmacy/', views.pharmacy_report, name='pharmacy_report'),
    path('laboratory/', views.lab_report, name='lab_report'),
    path('revenue-csv/', views.revenue_csv_export, name='revenue_csv_export'),
]
