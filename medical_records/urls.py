from django.urls import path
from . import views

urlpatterns = [
    path('', views.medical_records_dashboard, name='medical_records_dashboard'),
    path('patient/<int:patient_pk>/', views.patient_records, name='patient_records'),
    path('search/', views.search_records, name='search_records'),
    path('upload/<int:patient_pk>/', views.upload_record, name='upload_record'),
]
