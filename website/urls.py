from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('departments/', views.departments_page, name='departments_page'),
    path('doctors/', views.doctors_page, name='doctors_page'),
    path('diseases/', views.diseases, name='diseases'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('appointment/', views.appointment, name='appointment'),
    path('appointment-success/', views.appointment_success, name='appointment_success'),
]
