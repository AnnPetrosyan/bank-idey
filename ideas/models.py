from django.db import models
from django.contrib.auth.models import User
from accounts.models import Department

STATUS_CHOICES = [
    ('new', 'Новая'),
    ('review', 'На рассмотрении'),
    ('accepted', 'Принята к реализации'),
    ('in_progress', 'В работе'),
    ('done', 'Реализована'),
    ('rejected_by_manager', 'Отклонена руководителем'),
    ('rejected_by_expert', 'Отклонена экспертом'),
]


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Idea(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='authored_ideas',
    )
    status = models.CharField(
        max_length=24, choices=STATUS_CHOICES, default='new',
    )
    rejection_reason = models.TextField(blank=True, null=True)
    reviewer = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_ideas',
    )
    assigned_expert = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_ideas',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    BADGE_CLASS = {
        'new': 'badge-new', 'review': 'badge-review', 'accepted': 'badge-accepted',
        'in_progress': 'badge-progress', 'done': 'badge-done',
        'rejected_by_manager': 'badge-rej-mgr', 'rejected_by_expert': 'badge-rej-exp',
    }
    ACCENT_COLOR = {
        'new': '#635D8C', 'review': '#8D6608', 'accepted': '#2E5FDB',
        'in_progress': '#6D28D9', 'done': '#197F31',
        'rejected_by_manager': '#C9271D', 'rejected_by_expert': '#BE2982',
    }
    PERSON_CHIP_MAP = {
        'review': ('На рассмотрении у', 'reviewer'),
        'in_progress': ('В работе у', 'assigned_expert'),
        'accepted': ('Согласовал — руководитель', 'reviewer'),
        'rejected_by_manager': ('Отклонил — руководитель', 'reviewer'),
        'rejected_by_expert': ('Отклонил — эксперт', 'assigned_expert'),
        'done': ('Реализовал — эксперт', 'assigned_expert'),
    }

    @property
    def badge_class(self):
        return self.BADGE_CLASS.get(self.status, 'badge-new')

    @property
    def accent_color(self):
        return self.ACCENT_COLOR.get(self.status, '#635D8C')

    @property
    def person_chip(self):
        mapping = self.PERSON_CHIP_MAP.get(self.status)
        if not mapping:
            return None
        label, field_name = mapping
        user = getattr(self, field_name)
        if not user:
            return None
        return {'label': label, 'user': user, 'initials': _user_initials(user)}

    @property
    def author_initials(self):
        return _user_initials(self.author)

    def __str__(self):
        return self.title


def _user_initials(user):
    name = user.first_name or user.username
    parts = name.split()
    return (parts[0][0] if parts else '') + (parts[1][0] if len(parts) > 1 else '')