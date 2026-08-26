from django.db import models
from django.contrib.auth.models import User


ROLE_CHOICES = [
    ('employee', 'Сотрудник'),
    ('manager', 'Руководитель'),
    ('expert', 'Эксперт'),
    ('admin', 'Администратор'),
]


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    manager = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_department',
    )

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(
        Department, null=True, blank=True,
        on_delete=models.PROTECT,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    @property
    def initials(self):
        name = self.user.first_name or self.user.username
        parts = name.split()
        return (parts[0][0] if parts else '') + (parts[1][0] if len(parts) > 1 else '')

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'