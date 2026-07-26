from django.urls import path
from . import views

urlpatterns = [
    path('', views.blood_bank_dashboard, name='blood_bank_dashboard'),
    path('request/<int:pk>/', views.blood_request_detail, name='blood_request_detail'),
]
