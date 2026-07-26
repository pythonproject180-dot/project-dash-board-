from django.urls import path
from . import views

urlpatterns = [
    path('', views.ot_dashboard, name='ot_dashboard'),
    path('surgery/<int:pk>/', views.surgery_detail, name='surgery_detail'),
]
