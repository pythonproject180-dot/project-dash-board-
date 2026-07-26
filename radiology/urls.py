from django.urls import path
from . import views

urlpatterns = [
    path('', views.radiology_dashboard, name='radiology_dashboard'),
    path('queue/', views.radiology_queue, name='radiology_queue'),
    path('request/<int:pk>/', views.radiology_request_detail, name='radiology_request_detail'),
    path('search/', views.radiology_search, name='radiology_search'),
    path('report-pdf/<int:pk>/', views.radiology_report_pdf, name='radiology_report_pdf'),
    path('report-jpg/<int:pk>/', views.radiology_report_jpg, name='radiology_report_jpg'),
    path('catalog/', views.radiology_catalog_list, name='radiology_catalog_list'),
    path('catalog/add/', views.radiology_catalog_add, name='radiology_catalog_add'),
]
