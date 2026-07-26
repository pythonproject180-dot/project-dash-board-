from django.urls import path
from . import views

urlpatterns = [
    path('', views.insurance_dashboard, name='insurance_dashboard'),
    path('insurers/', views.insurer_list, name='insurer_list'),
    path('insurers/add/', views.insurer_add, name='insurer_add'),
    path('claim/submit/', views.claim_submit, name='claim_submit'),
    path('claim/<int:pk>/', views.claim_review, name='claim_review'),
    path('claim-pdf/<int:pk>/', views.claim_receipt_pdf, name='claim_receipt_pdf'),
    path('claim-jpg/<int:pk>/', views.claim_receipt_jpg, name='claim_receipt_jpg'),
    path('claims/report/', views.claims_report, name='claims_report'),
]
