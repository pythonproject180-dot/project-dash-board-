from django.urls import path
from . import views

urlpatterns = [
    path('', views.nursing_dashboard, name='nursing_dashboard'),
    path('note/<int:patient_pk>/', views.add_nursing_note, name='add_nursing_note'),
    path('patient/<int:patient_pk>/', views.nursing_patient_history, name='nursing_patient_history'),
]
