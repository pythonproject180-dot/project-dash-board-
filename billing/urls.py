from django.urls import path
from . import views

urlpatterns = [
    path('', views.cash_counter_dashboard, name='cash_counter_dashboard'),
    path('create/', views.create_bill, name='create_bill'),
    path('search/', views.bill_search, name='bill_search'),
    path('detail/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_add, name='service_add'),
    path('today/', views.today_collections, name='today_collections'),
    path('autocomplete/', views.service_autocomplete, name='service_autocomplete'),
    path('receipt-pdf/<int:pk>/', views.bill_receipt_pdf_view, name='bill_receipt_pdf_view'),
    path('receipt-jpg/<int:pk>/', views.bill_receipt_jpg_view, name='bill_receipt_jpg_view'),
]
