from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.appointment_book, name='appointment_book'),
]
