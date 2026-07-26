from django.urls import path
from . import views

urlpatterns = [
    path('', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.medicine_add, name='medicine_add'),
    path('dispense/', views.pharmacy_dispense, name='pharmacy_dispense'),
    path('report/', views.pharmacy_report, name='pharmacy_report'),
]
