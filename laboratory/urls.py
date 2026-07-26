from django.urls import path
from . import views

urlpatterns = [
    path('', views.lab_dashboard, name='lab_dashboard'),
    path('queue/', views.lab_queue, name='lab_queue'),
    path('request/<int:pk>/', views.lab_request_detail, name='lab_request_detail'),
    path('search/', views.lab_search, name='lab_search'),
    path('report-pdf/<int:pk>/', views.lab_report_pdf, name='lab_report_pdf'),
    path('report-jpg/<int:pk>/', views.lab_report_jpg, name='lab_report_jpg'),
    path('catalog/', views.lab_catalog_list, name='lab_catalog_list'),
    path('catalog/add/', views.lab_catalog_add, name='lab_catalog_add'),
]
