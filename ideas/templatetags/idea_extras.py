from django import template

register = template.Library()


def plural_idea(n):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return 'идея'
    if 2 <= n10 <= 4 and (n100 < 10 or n100 >= 20):
        return 'идеи'
    return 'идей'


def plural_employee(n):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return 'сотрудник'
    if 2 <= n10 <= 4 and (n100 < 10 or n100 >= 20):
        return 'сотрудника'
    return 'сотрудников'


register.filter('plural_idea', plural_idea)
register.filter('plural_employee', plural_employee)