from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from ideas.templatetags.idea_extras import plural_employee

from .mixins import AdminRequiredMixin
from .models import Department, ROLE_CHOICES
from .forms import UserCreateForm, UserEditForm, DepartmentForm


def _mark_errors(form):
    for name in form.fields:
        if form[name].errors:
            widget = form.fields[name].widget
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = (existing + ' bad').strip()


def _require_admin(request):
    if not request.user.is_authenticated or request.user.profile.role != 'admin':
        return HttpResponseForbidden('Доступ запрещён — требуется роль администратора')
    return None


class UserListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/users.html'
    ROLE_LABELS = dict(ROLE_CHOICES)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_filter = self.request.GET.get('role', '')
        dept_filter = self.request.GET.get('department', '')

        qs = User.objects.select_related('profile', 'profile__department').order_by('username')
        if role_filter:
            qs = qs.filter(profile__role=role_filter)
        if dept_filter:
            qs = qs.filter(profile__department_id=dept_filter)

        role_counts = {}
        for u in User.objects.select_related('profile'):
            role_counts[u.profile.role] = role_counts.get(u.profile.role, 0) + 1

        context['users'] = qs
        context['total_users'] = User.objects.count()
        context['role_counts'] = [
            {'value': r, 'label': self.ROLE_LABELS[r], 'count': role_counts[r]}
            for r in self.ROLE_LABELS if role_counts.get(r)
        ]
        context['role_filter'] = role_filter
        context['dept_filter'] = dept_filter
        context['filters_active'] = bool(role_filter or dept_filter)
        context['departments'] = Department.objects.all()
        context['role_choices'] = ROLE_CHOICES
        context['last_created_password'] = self.request.session.pop('last_created_password', None)
        return context


def user_add(request):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user, password = form.save()
            request.session['last_created_password'] = password
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('admin-users')
            return response
        _mark_errors(form)
    else:
        form = UserCreateForm()
    return render(request, 'admin/_add_user_modal.html', {'form': form})


def user_edit(request, pk):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST)
        if form.is_valid():
            form.save(target)
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('admin-users')
            return response
        _mark_errors(form)
    else:
        form = UserEditForm(initial={
            'full_name': target.first_name,
            'department': target.profile.department,
        })
    return render(request, 'admin/_edit_user_modal.html', {'form': form, 'target': target})


def user_delete(request, pk):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        return HttpResponseForbidden('Нельзя удалить собственную учётную запись')
    if request.method == 'POST':
        target.delete()
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('admin-users')
        return response
    return render(request, 'admin/_delete_user_modal.html', {'target': target})


class DepartmentListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/departments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departments = Department.objects.annotate(
            emp_count=Count('profile', distinct=True),
            idea_count=Count('idea', distinct=True),
        ).order_by('name')
        context['departments'] = departments
        context['total_assigned'] = User.objects.filter(profile__department__isnull=False).count()
        return context


def department_add(request):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Введите название отдела')
    elif Department.objects.filter(name__iexact=name).exists():
        messages.error(request, 'Такой отдел уже есть')
    else:
        Department.objects.create(name=name)
        messages.success(request, 'Отдел добавлен')
    return redirect('admin-departments')


def department_delete(request, pk):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    department = get_object_or_404(Department, pk=pk)
    emp_count = User.objects.filter(profile__department=department).count()
    if emp_count > 0:
        messages.error(request, f'Нельзя удалить — в отделе {emp_count} {plural_employee(emp_count)}')
        return redirect('admin-departments')
    try:
        department.delete()
        messages.success(request, 'Отдел удалён')
    except ProtectedError:
        messages.error(request, 'Нельзя удалить — на этот отдел ссылаются существующие идеи')
    return redirect('admin-departments')