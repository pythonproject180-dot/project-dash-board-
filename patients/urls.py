from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.registration_dashboard, name='registration_dashboard'),
    path('list/', views.patient_list, name='patient_list'),
    path('register/', views.patient_register, name='patient_register'),
    path('edit/<int:pk>/', views.patient_edit, name='patient_edit'),
    path('delete/<int:pk>/', views.patient_delete, name='patient_delete'),
    path('detail/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('search/', views.patient_search, name='patient_search'),
    path('patient-card/<int:pk>/', views.patient_card, name='patient_card'),
    path('patient-card-pdf/<int:pk>/', views.patient_card_pdf, name='patient_card_pdf'),
    path('patient-card-jpg/<int:pk>/', views.patient_card_jpg, name='patient_card_jpg'),
    path('opd-ticket-pdf/<int:pk>/', views.opd_ticket_pdf, name='opd_ticket_pdf'),
    path('opd-ticket-jpg/<int:pk>/', views.opd_ticket_jpg, name='opd_ticket_jpg'),
    path('bill-pdf/<int:pk>/', views.bill_receipt_pdf, name='bill_receipt_pdf'),
    path('bill-jpg/<int:pk>/', views.bill_receipt_jpg, name='bill_receipt_jpg'),
]
