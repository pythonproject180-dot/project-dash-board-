from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('quota/', views.doctor_manage_quota, name='doctor_manage_quota'),
    path('consultation/<int:visit_pk>/', views.consultation_create, name='consultation_create'),
    path('list/', views.doctor_list, name='doctor_list'),
    path('add/', views.doctor_add, name='doctor_add'),
    path('edit/<int:pk>/', views.doctor_edit, name='doctor_edit'),
    path('delete/<int:pk>/', views.doctor_delete, name='doctor_delete'),
]
