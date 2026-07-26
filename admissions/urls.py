from django.urls import path
from . import views

urlpatterns = [
    path('', views.admission_dashboard, name='admission_dashboard'),
    path('list/', views.admission_list, name='admission_list'),
    path('admit/', views.admit_patient, name='admit_patient'),
    path('discharge/<int:pk>/', views.discharge_patient, name='discharge_patient'),
    path('search/', views.admission_search, name='admission_search'),
    path('discharge-summary-pdf/<int:pk>/', views.discharge_summary_pdf, name='discharge_summary_pdf'),
    path('discharge-summary-jpg/<int:pk>/', views.discharge_summary_jpg, name='discharge_summary_jpg'),
]
