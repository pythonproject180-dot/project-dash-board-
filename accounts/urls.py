from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-success/', views.login_success, name='login_success'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.add_staff, name='add_staff'),
]
