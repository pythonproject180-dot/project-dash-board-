from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.portal_signup, name='portal_signup'),
    path('login/', views.portal_login, name='portal_login'),
    path('forgot-password/', views.portal_forgot_password, name='portal_forgot_password'),
    path('dashboard/', views.portal_dashboard, name='portal_dashboard'),
    path('appointment/', views.portal_appointment, name='portal_appointment'),
    path('logout/', views.portal_logout, name='portal_logout'),
]
