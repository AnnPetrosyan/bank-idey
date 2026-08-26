from django import forms
from accounts.models import Department
from .models import Category, Idea


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class IdeaForm(forms.ModelForm):
    title = forms.CharField(
        label='Название', max_length=200,
        widget=forms.TextInput(attrs={'class': 'input'}),
        error_messages={'required': 'Заполните название идеи'})
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(), label='Отдел', empty_label=None,
        widget=forms.Select(attrs={'class': 'select'}),
        error_messages={'required': 'Выберите отдел'})
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True), label='Категория',
        empty_label='Выберите категорию',
        widget=forms.Select(attrs={'class': 'select'}),
        error_messages={'required': 'Категория обязательна'})
    description = forms.CharField(
        label='Описание — проблема и предлагаемое решение',
        widget=forms.Textarea(attrs={'class': 'input', 'style': 'height:120px;'}),
        error_messages={'required': 'Опишите проблему и решение'})

    class Meta:
        model = Idea
        fields = ['title', 'department', 'category', 'description']


class IdeaDecisionForm(forms.Form):
    reason = forms.CharField(
        label='Причина отклонения',
        widget=forms.Textarea(attrs={'class': 'input', 'style': 'height:120px;'}),
        required=True,
    )