from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin'

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("Доступ запрещён — требуется роль администратора")