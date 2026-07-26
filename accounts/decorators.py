from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    """Decorator that checks if the user has one of the allowed roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/accounts/login/')
            if request.user.is_superuser or request.user.role == 'super_admin':
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return redirect(request.user.get_dashboard_url())
        return _wrapped_view
    return decorator

# Convenience decorators for each role
super_admin_required = role_required(['super_admin'])
registration_required = role_required(['registration', 'super_admin'])
cash_counter_required = role_required(['cash_counter', 'super_admin'])
doctor_required = role_required(['doctor', 'super_admin'])
pharmacy_required = role_required(['pharmacy', 'super_admin'])
laboratory_required = role_required(['laboratory', 'super_admin'])
radiology_required = role_required(['radiology', 'super_admin'])
insurance_required = role_required(['insurance', 'super_admin'])
admission_required = role_required(['admission', 'super_admin'])
nursing_required = role_required(['nursing', 'super_admin'])
ot_required = role_required(['operation_theatre', 'super_admin'])
blood_bank_required = role_required(['blood_bank', 'super_admin'])
accounts_required = role_required(['accounts', 'super_admin'])
medical_records_required = role_required(['medical_records', 'super_admin'])
clinical_only = role_required(['doctor', 'nursing', 'super_admin'])  # Can view/edit clinical but not financial
financial_only = role_required(['cash_counter', 'accounts', 'insurance', 'super_admin'])  # Can view financial
