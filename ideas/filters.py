import django_filters
from django import forms
from accounts.models import Department
from .models import Idea, Category


class IdeaFilter(django_filters.FilterSet):
    department = django_filters.ModelChoiceFilter(
        queryset=Department.objects.all(),
        empty_label='Все отделы',
        widget=forms.Select(attrs={'class': 'select'}))
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        empty_label='Все категории',
        widget=forms.Select(attrs={'class': 'select'}))

    class Meta:
        model = Idea
        fields = ['department', 'category']