from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:visit_pk>/', views.consultation_create, name='consultation_create'),
]
