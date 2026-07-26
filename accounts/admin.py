from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AuditLog, Province, District

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'role', 'phone', 'is_active_staff', 'is_staff']
    list_filter = ['role', 'is_active_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Info', {'fields': ('role', 'phone', 'is_active_staff')}),
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'module', 'patient_id']
    list_filter = ['module']
    readonly_fields = ['timestamp', 'user', 'action', 'module', 'detail', 'patient_id']

@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'province']
