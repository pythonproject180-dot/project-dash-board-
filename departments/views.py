from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Department
from accounts.models import AuditLog

@login_required
def department_list(request):
    if not (request.user.role == 'super_admin' or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())
    departments = Department.objects.all()
    return render(request, 'dashboard/department_list.html', {'departments': departments, 'role': 'super_admin'})

@login_required
def department_add(request):
    if not (request.user.role == 'super_admin' or request.user.is_superuser):
        return redirect(request.user.get_dashboard_url())
    if request.method == 'POST':
        dept = Department.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            consultation_fee=request.POST.get('consultation_fee', 0),
            photo=request.FILES.get('photo'),
        )
        AuditLog.objects.create(user=request.user, action='Create Department', module='departments', detail=dept.name)
        return redirect('/departments/')
    return render(request, 'dashboard/department_form.html', {'role': 'super_admin', 'action': 'Add'})

@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.name = request.POST.get('name')
        dept.description = request.POST.get('description')
        dept.consultation_fee = request.POST.get('consultation_fee', 0)
        if request.FILES.get('photo'):
            dept.photo = request.FILES.get('photo')
        dept.save()
        AuditLog.objects.create(user=request.user, action='Edit Department', module='departments', detail=dept.name)
        return redirect('/departments/')
    return render(request, 'dashboard/department_form.html', {'department': dept, 'role': 'super_admin', 'action': 'Edit'})

@login_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    AuditLog.objects.create(user=request.user, action='Delete Department', module='departments', detail=dept.name)
    dept.delete()
    return redirect('/departments/')
