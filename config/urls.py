from django.views.generic.base import RedirectView
from accounts.forms import StyledLoginForm
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from ideas.views import (
    IdeaListView, IdeaCreateView, IdeaDetailView,
    MyIdeasView, MyReviewsView, MyWorkView, ProfileView, TopAuthorsView,
    CategoryListView, category_add, category_delete, AdminStatsView, god_mode,
    idea_actions, idea_take_review, idea_approve, idea_reject,
    idea_take_work, idea_complete, idea_reject_unrealizable,
)
from accounts.views import (
    UserListView, user_add, user_edit, user_delete,
    DepartmentListView, department_add, department_delete,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html', authentication_form=StyledLoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('ideas/', IdeaListView.as_view(), name='idea-list'),
    path('ideas/new/', IdeaCreateView.as_view(), name='idea-create'),
    path('ideas/<int:pk>/', IdeaDetailView.as_view(), name='idea-detail'),
    path('ideas/<int:pk>/actions/', idea_actions, name='idea-actions'),
    path('ideas/<int:pk>/take-review/', idea_take_review, name='idea-take-review'),
    path('ideas/<int:pk>/approve/', idea_approve, name='idea-approve'),
    path('ideas/<int:pk>/reject/', idea_reject, name='idea-reject'),
    path('ideas/<int:pk>/take-work/', idea_take_work, name='idea-take-work'),
    path('ideas/<int:pk>/complete/', idea_complete, name='idea-complete'),
    path('ideas/<int:pk>/reject-unrealizable/', idea_reject_unrealizable, name='idea-reject-unrealizable'),
    path('my/', MyIdeasView.as_view(), name='my-ideas'),
    path('my-reviews/', MyReviewsView.as_view(), name='my-reviews'),
    path('my-work/', MyWorkView.as_view(), name='my-work'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('top-authors/', TopAuthorsView.as_view(), name='top-authors'),
    path('manage/users/', UserListView.as_view(), name='admin-users'),
    path('manage/users/add/', user_add, name='admin-user-add'),
    path('manage/users/<int:pk>/edit/', user_edit, name='admin-user-edit'),
    path('manage/users/<int:pk>/delete/', user_delete, name='admin-user-delete'),
    path('manage/categories/', CategoryListView.as_view(), name='admin-categories'),
    path('manage/categories/add/', category_add, name='admin-category-add'),
    path('manage/categories/<int:pk>/delete/', category_delete, name='admin-category-delete'),
    path('manage/departments/', DepartmentListView.as_view(), name='admin-departments'),
    path('manage/departments/add/', department_add, name='admin-department-add'),
    path('manage/departments/<int:pk>/delete/', department_delete, name='admin-department-delete'),
    path('manage/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('manage/god-mode/', god_mode, name='admin-god-mode'),
    path('', RedirectView.as_view(pattern_name='idea-list', permanent=False)),
]