from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Department
from ideas.models import Category, Idea


class Command(BaseCommand):
    help = 'Загружает демонстрационные данные проекта (безопасно перезапускать)'

    def handle(self, *args, **options):
        dept_sales, _ = Department.objects.get_or_create(name='Отдел продаж')
        dept_it, _ = Department.objects.get_or_create(name='IT-отдел')

        cat_process, _ = Category.objects.get_or_create(name='Оптимизация процессов')
        cat_it, _ = Category.objects.get_or_create(name='IT и автоматизация')
        cat_service, _ = Category.objects.get_or_create(name='Клиентский сервис')

        users_data = [
            ('manager_sales', 'Руководитель Продаж', 'manager', dept_sales),
            ('manager_it', 'Руководитель IT', 'manager', dept_it),
            ('employee_sales', 'Сотрудник Продаж', 'employee', dept_sales),
            ('employee_it', 'Сотрудник IT', 'employee', dept_it),
            ('expert_1', 'Эксперт Первый', 'expert', dept_sales),
            ('expert_2', 'Эксперт Второй', 'expert', dept_it),
        ]
        users = {}
        for username, full_name, role, dept in users_data:
            user, created = User.objects.get_or_create(
                username=username, defaults={'first_name': full_name})
            if created:
                user.set_password('demo12345')
                user.save()
            user.profile.role = role
            user.profile.department = dept
            user.profile.save()
            users[username] = user
            self.stdout.write(f'  {"создан" if created else "уже есть"}: {username}')

        # reviewer/assigned_expert для идей, где статус подразумевает их
        # наличие, но таблица документа явно их не перечисляла —
        # дозаполнено для целостности данных, не буквальная цитата документа
        ideas_data = [
            dict(title='Сократить время согласования заявок в IT',
                 department=dept_it, category=cat_process,
                 author=users['employee_it'], status='review',
                 reviewer=users['manager_sales']),
            dict(title='Автоматизировать сверку остатков',
                 department=dept_sales, category=cat_it,
                 author=users['employee_sales'], status='in_progress',
                 reviewer=users['manager_sales'], assigned_expert=users['expert_1']),
            dict(title='Перенести отчёты в единую таблицу',
                 department=dept_sales, category=cat_process,
                 author=users['employee_sales'], status='new'),
            dict(title='Внедрить чат-бота для клиентской поддержки',
                 department=dept_it, category=cat_service,
                 author=users['employee_it'], status='accepted',
                 reviewer=users['manager_it']),
            dict(title='Единый шаблон коммерческого предложения',
                 department=dept_sales, category=cat_process,
                 author=users['manager_sales'], status='new'),
            dict(title='Настроить мониторинг серверов',
                 department=dept_it, category=cat_it,
                 author=users['expert_2'], status='new'),
            dict(title='Сократить время ответа на обращения клиентов',
                 department=dept_sales, category=cat_service,
                 author=users['employee_sales'], status='rejected_by_manager',
                 reviewer=users['manager_sales'],
                 rejection_reason='Дублирует уже запущенную инициативу'),
            dict(title='Автоматически генерировать акты сверки',
                 department=dept_it, category=cat_it,
                 author=users['employee_it'], status='rejected_by_expert',
                 reviewer=users['manager_it'], assigned_expert=users['expert_1'],
                 rejection_reason='Требует интеграции с внешней системой, которой нет в контуре компании'),
            dict(title='Единая база знаний по продуктам',
                 department=dept_sales, category=cat_service,
                 author=users['employee_sales'], status='done',
                 reviewer=users['manager_sales'], assigned_expert=users['expert_2']),
            dict(title='Перевести встречи отдела в единый календарь',
                 department=dept_it, category=cat_process,
                 author=users['manager_it'], status='new'),
        ]
        for data in ideas_data:
            title = data.pop('title')
            idea, created = Idea.objects.get_or_create(
                title=title,
                defaults={**data, 'description': 'Демонстрационная идея для тестирования.'})
            self.stdout.write(f'  {"создана" if created else "уже есть"}: {title}')

        self.stdout.write(self.style.SUCCESS('Готово.'))