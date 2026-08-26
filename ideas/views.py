from django.db.models import Count
from accounts.views import _require_admin
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.urls import reverse_lazy, reverse

from django.contrib.auth.models import User
from accounts.mixins import AdminRequiredMixin
from accounts.models import Department
from .models import Idea, Category, STATUS_CHOICES
from .forms import IdeaForm, IdeaDecisionForm
from .filters import IdeaFilter


BADGE_COLORS = {
    'new': 'd-new', 'review': 'd-review', 'accepted': 'd-accepted',
    'in_progress': 'd-progress', 'done': 'd-done',
    'rejected_by_manager': 'd-rej-mgr', 'rejected_by_expert': 'd-rej-exp',
}

# соответствие ?from=... из ссылки → (маршрут для крошки, подпись крошки)
BACK_MAP = {
    'my-ideas': ('my-ideas', 'Назад к моим идеям'),
    'my-reviews': ('my-reviews', 'Назад к моим решениям'),
    'my-work': ('my-work', 'Назад к моим идеям в работе'),
}


def _status_stats(base_qs):
    by_status = []
    for value, label in STATUS_CHOICES:
        count = base_qs.filter(status=value).count()
        if count:
            by_status.append({'value': value, 'label': label, 'count': count, 'color': BADGE_COLORS[value]})
    return {'total': base_qs.count(), 'by_status': by_status}


def _get_back_from(request):
    return request.GET.get('from', '')


def _redirect_to_detail(request, pk):
    """Общий возврат на карточку идеи после любого действия — сохраняет,
    с какого именно списка пришёл пользователь (?from=...), а не всегда
    ведёт на общий список."""
    url = reverse('idea-detail', kwargs={'pk': pk})
    back_from = _get_back_from(request)
    if back_from:
        url += f'?from={back_from}'
    if request.headers.get('HX-Request') == 'true':
        response = HttpResponse(status=204)
        response['HX-Redirect'] = url
        return response
    return redirect(url)


class AdminCheckView(AdminRequiredMixin, View):
    def get(self, request):
        return HttpResponse("Доступ разрешён — вы администратор")


class IdeaListView(LoginRequiredMixin, ListView):
    model = Idea
    context_object_name = 'ideas'
    ordering = ['-created_at']
    paginate_by = 9

    def get_queryset(self):
        qs = super().get_queryset()
        self.filterset = IdeaFilter(self.request.GET, queryset=qs)
        self.filterset.form.fields['category'].label_from_instance = \
            lambda obj: f'{obj.name} (архив)' if not obj.is_active else obj.name
        qs = self.filterset.qs
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['stats'] = _status_stats(self.filterset.qs)
        context['list_url_name'] = 'idea-list'
        context['show_author'] = True
        return context

    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            if self.request.headers.get('HX-Target') == 'load-more-row':
                return ['ideas/_idea_items.html']
            return ['ideas/_idea_page_body.html']
        return ['ideas/list.html']


class IdeaCreateView(LoginRequiredMixin, CreateView):
    model = Idea
    form_class = IdeaForm
    template_name = 'ideas/form.html'
    success_url = reverse_lazy('idea-list')

    def get_initial(self):
        initial = super().get_initial()
        initial['department'] = self.request.user.profile.department
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        for name in form.fields:
            if form[name].errors:
                widget = form.fields[name].widget
                existing = widget.attrs.get('class', '')
                widget.attrs['class'] = (existing + ' bad').strip()
        return super().form_invalid(form)


class IdeaDetailView(LoginRequiredMixin, DetailView):
    model = Idea
    template_name = 'ideas/detail.html'
    context_object_name = 'idea'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_from = _get_back_from(self.request)
        url_name, label = BACK_MAP.get(back_from, ('idea-list', 'Назад к списку идей'))
        context['back_url'] = reverse(url_name)
        context['back_label'] = label
        context['back_from'] = back_from
        return context


def idea_actions(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    return render(request, 'ideas/_idea_actions.html', {'idea': idea, 'back_from': _get_back_from(request)})


def idea_take_review(request, pk):
    updated = Idea.objects.filter(
        pk=pk, status='new', reviewer__isnull=True
    ).update(reviewer=request.user, status='review')
    if not updated:
        messages.error(request, 'Идею нельзя взять на рассмотрение (уже занята или не в статусе «Новая»)')
    return _redirect_to_detail(request, pk)


def idea_approve(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if idea.reviewer != request.user:
        return HttpResponseForbidden('Только руководитель, взявший идею на рассмотрение, может её одобрить')
    idea.status = 'accepted'
    idea.save()
    return _redirect_to_detail(request, pk)


def idea_reject(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if idea.reviewer != request.user:
        return HttpResponseForbidden('Только руководитель, взявший идею на рассмотрение, может её отклонить')
    if request.method == 'POST':
        form = IdeaDecisionForm(request.POST)
        if form.is_valid():
            idea.status = 'rejected_by_manager'
            idea.rejection_reason = form.cleaned_data['reason']
            idea.save()
            return _redirect_to_detail(request, pk)
    else:
        form = IdeaDecisionForm()
    return render(request, 'ideas/_idea_actions.html', {
        'idea': idea, 'reject_form': form, 'show_reject_form': True, 'back_from': _get_back_from(request),
    })


def idea_take_work(request, pk):
    updated = Idea.objects.filter(
        pk=pk, status='accepted', assigned_expert__isnull=True
    ).update(assigned_expert=request.user, status='in_progress')
    if not updated:
        messages.error(request, 'Идею нельзя взять в работу (уже занята или не в статусе «Принята к реализации»)')
    return _redirect_to_detail(request, pk)


def idea_complete(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if idea.assigned_expert != request.user:
        return HttpResponseForbidden('Только эксперт, взявший идею в работу, может её завершить')
    idea.status = 'done'
    idea.save()
    return _redirect_to_detail(request, pk)


def idea_reject_unrealizable(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if idea.assigned_expert != request.user:
        return HttpResponseForbidden('Только эксперт, взявший идею в работу, может её отклонить')
    if request.method == 'POST':
        form = IdeaDecisionForm(request.POST)
        if form.is_valid():
            idea.status = 'rejected_by_expert'
            idea.rejection_reason = form.cleaned_data['reason']
            idea.save()
            return _redirect_to_detail(request, pk)
    else:
        form = IdeaDecisionForm()
    return render(request, 'ideas/_idea_actions.html', {
        'idea': idea, 'reject_form': form, 'show_reject_form': True, 'back_from': _get_back_from(request),
    })


class PersonalIdeaListView(LoginRequiredMixin, ListView):
    model = Idea
    context_object_name = 'ideas'
    paginate_by = 9
    person_field = None
    url_name = None
    template = None
    empty_message_base = ''
    show_author = True
    show_empty_cta = True

    def get_base_qs(self):
        return Idea.objects.filter(**{self.person_field: self.request.user})

    def get_queryset(self):
        qs = self.get_base_qs().order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_base_qs()
        context['stats'] = _status_stats(base_qs)
        context['list_url_name'] = self.url_name
        context['show_author'] = self.show_author
        if self.request.GET.get('status'):
            context['empty_message'] = 'Под выбранный статус не подходит ни одна идея.'
        else:
            context['empty_message'] = self.empty_message_base
            if self.show_empty_cta:
                context['empty_cta_url'] = reverse('idea-list')
                context['empty_cta_label'] = 'Перейти к общему списку →'
        return context

    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            if self.request.headers.get('HX-Target') == 'load-more-row':
                return ['ideas/_idea_items.html']
            return ['ideas/_idea_page_body.html']
        return [self.template]


class MyIdeasView(PersonalIdeaListView):
    person_field = 'author'
    url_name = 'my-ideas'
    template = 'ideas/my.html'
    empty_message_base = 'У вас пока нет идей.'
    show_author = False
    show_empty_cta = False


class MyReviewsView(PersonalIdeaListView):
    person_field = 'reviewer'
    url_name = 'my-reviews'
    template = 'ideas/my_reviews.html'
    empty_message_base = 'Вы пока не взяли ни одной идеи на рассмотрение.'


class MyWorkView(PersonalIdeaListView):
    person_field = 'assigned_expert'
    url_name = 'my-work'
    template = 'ideas/my_work.html'
    empty_message_base = 'Вы пока не взяли ни одной идеи в работу.'
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.profile.role == 'admin':
            context['is_admin'] = True
            return context
        mine = Idea.objects.filter(author=self.request.user).order_by('-created_at')
        context['mine_count'] = mine.count()
        context['approved_count'] = mine.filter(
            status__in=['accepted', 'in_progress', 'done']).count()
        context['stats'] = _status_stats(mine)
        context['recent_ideas'] = mine[:5]
        return context
class TopAuthorsView(LoginRequiredMixin, TemplateView):
    template_name = 'ideas/top_authors.html'
    APPROVED_STATUSES = ['accepted', 'in_progress', 'done']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.request.GET.get('mode', 'count')
        dept_id = self.request.GET.get('department') or None
        cat_id = self.request.GET.get('category') or None

        qs = Idea.objects.all()
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if cat_id:
            qs = qs.filter(category_id=cat_id)

        counts, approved = {}, {}
        for idea in qs.values('author_id', 'status'):
            counts[idea['author_id']] = counts.get(idea['author_id'], 0) + 1
            if idea['status'] in self.APPROVED_STATUSES:
                approved[idea['author_id']] = approved.get(idea['author_id'], 0) + 1

        author_ids = list(counts.keys())
        authors = {
            u.id: u for u in User.objects.filter(id__in=author_ids)
            .select_related('profile', 'profile__department')
        }

        def score_of(uid):
            return approved.get(uid, 0) if mode == 'approved' else counts.get(uid, 0)

        sorted_ids = sorted(author_ids, key=lambda uid: -score_of(uid))
        max_score = score_of(sorted_ids[0]) if sorted_ids else 0

        rows = []
        prev_score, prev_rank = None, 0
        for idx, uid in enumerate(sorted_ids):
            score = score_of(uid)
            rank = prev_rank if score == prev_score else idx + 1
            prev_rank, prev_score = rank, score
            user = authors[uid]
            pct = max(6, round(score / max_score * 100)) if max_score > 0 else 0
            rows.append({
                'rank': rank, 'user': user, 'score': score, 'pct': pct,
                'is_top': rank == 1, 'is_me': uid == self.request.user.id,
                'initials': user.profile.initials,
                'department': user.profile.department,
            })

        context.update({
            'rows': rows, 'mode': mode,
            'departments': Department.objects.all(),
            'categories': Category.objects.all(),
            'selected_dept': int(dept_id) if dept_id else None,
            'selected_cat': int(cat_id) if cat_id else None,
            'filters_active': bool(dept_id or cat_id),
        })
        return context
class CategoryListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True) \
            .annotate(idea_count=Count('idea')).order_by('name')
        context['total_ideas'] = Idea.objects.count()
        return context


def category_add(request):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Введите название категории')
    elif Category.objects.filter(name__iexact=name, is_active=True).exists():
        messages.error(request, 'Такая категория уже есть')
    else:
        Category.objects.create(name=name)
        messages.success(request, 'Категория добавлена')
    return redirect('admin-categories')


def category_delete(request, pk):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden
    category = get_object_or_404(Category, pk=pk)
    if Idea.objects.filter(category=category).exists():
        category.is_active = False
        category.save()
    else:
        category.delete()
    messages.success(request, 'Категория удалена')
    return redirect('admin-categories')
class AdminStatsView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approved_total = Idea.objects.filter(status__in=['accepted', 'in_progress', 'done']).count()

        by_dept = [
            {'name': d.name, 'count': Idea.objects.filter(department=d).count()}
            for d in Department.objects.all()
        ]
        by_cat = []
        for c in Category.objects.all().order_by('-is_active', 'name'):
            count = Idea.objects.filter(category=c).count()
            if count > 0:
                by_cat.append({'name': c.name, 'count': count, 'archived': not c.is_active})
        author_counts = {}
        for row in Idea.objects.values('author_id'):
            author_counts[row['author_id']] = author_counts.get(row['author_id'], 0) + 1
        top_ids = sorted(author_counts, key=lambda k: -author_counts[k])[:3]
        users_map = {u.id: u for u in User.objects.filter(id__in=top_ids)}
        top_authors = [
            {'name': users_map[uid].first_name or users_map[uid].username, 'count': author_counts[uid]}
            for uid in top_ids
        ]

        context.update({
            'total': Idea.objects.count(),
            'total_users': User.objects.count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'approved_total': approved_total,
            'status_stats': _status_stats(Idea.objects.all()),
            'by_dept': by_dept,
            'by_cat': by_cat,
            'top_authors': top_authors,
        })
        return context
def god_mode(request):
    forbidden = _require_admin(request)
    if forbidden:
        return forbidden

    idea_id = request.POST.get('idea_id') or request.GET.get('idea_id')
    idea = Idea.objects.filter(pk=idea_id).first() if idea_id else None
    if not idea:
        idea = Idea.objects.order_by('-created_at').first()

    if request.method == 'POST' and idea:
        idea.status = request.POST.get('new_status')
        idea.save()
        messages.success(request, 'Статус изменён в обход обычного потока («режим бога»)')
        return redirect(f"{reverse('admin-god-mode')}?idea_id={idea.pk}")

    return render(request, 'admin/god_mode.html', {
        'ideas': Idea.objects.order_by('-created_at'),
        'selected_idea': idea,
        'status_choices': STATUS_CHOICES,
    })