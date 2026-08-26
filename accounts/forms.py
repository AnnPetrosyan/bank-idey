import re
import secrets
import string

from django import forms
from django.contrib.auth.models import User

from .models import Department, ROLE_CHOICES


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'input'})}


class UserCreateForm(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}))
    full_name = forms.CharField(
        label='ФИО', max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}))
    role = forms.ChoiceField(
        label='Роль', choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'select'}))
    department = forms.ModelChoiceField(
        label='Отдел', queryset=Department.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'select'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if not username:
            raise forms.ValidationError('Укажите логин')
        if not re.match(r'^[a-z0-9_.]+$', username):
            raise forms.ValidationError('Только латинские буквы, цифры, точка и подчёркивание')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Такой логин уже занят')
        return username

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if not name:
            raise forms.ValidationError('Укажите ФИО')
        return name

    def save(self):
        password = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=password,
            first_name=self.cleaned_data['full_name'],
        )
        role = self.cleaned_data['role']
        user.profile.role = role
        if role in ('employee', 'manager', 'expert'):
            user.profile.department = self.cleaned_data.get('department')
        user.profile.save()
        return user, password


class UserEditForm(forms.Form):
    full_name = forms.CharField(
        label='ФИО', max_length=150,
        widget=forms.TextInput(attrs={'class': 'input'}))
    department = forms.ModelChoiceField(
        label='Отдел', queryset=Department.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'select'}))

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if not name:
            raise forms.ValidationError('ФИО не может быть пустым')
        return name

    def save(self, user):
        user.first_name = self.cleaned_data['full_name']
        user.save()
        if user.profile.role in ('employee', 'manager', 'expert'):
            user.profile.department = self.cleaned_data.get('department')
            user.profile.save()
        return user