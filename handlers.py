#!/usr/bin/env python3.9
"""
Handler - функция, оторая принимает на вход text (входящего сообщения) и context (dict), а возвращает bool:
True если шаг пройден, False если данные введены не верно.
"""
import re

# скомпилируем наши регулярные вырожения в объекты, чтобы использовать их дальше.
# Выражение в котором от начала ^ до конца строки $ занимает от 3 до 40 символов.
# В нем могут быть использованы любые буквы, цифры \w дефисы \- пробел \s
from generate_ticket import generate_ticket

re_name = re.compile(r'^[\w\-\s]{3,40}$')
# \b позволяет выдергивать это выражение из контекста, т.е. отдеять его из строки
re_email = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')


# context словарь в котором хранятся все данные которые мы набрали в ходе сценария,
# после завершения его context сбросится
def handle_name(text, context):
    # проверка совпадает ли наша строка с нашими ожиданиями.
    match = re.match(re_name, text)
    # если все совпало, то в контекст добавим text с ключом name и вернем True
    if match:
        context['name'] = text
        return True
    else:
        return False


def handle_email(text, context):
    # найдет все совпадения даже если email-ов во фразе больше одного, т.е. ответов может быть несколько
    matches = re.findall(re_email, text)
    # если есть хоть одно совпадение, в email запишем первое найденное совпадение
    if len(matches) > 0:
        context['email'] = matches[0]
        return True
    else:
        return False


def generate_ticket_handler(text, context):
    # вся функция этого хэндлера заключается в том, чтобы вызвать фунцию generate_ticket, чтобы в сценарии
    # подставился наш билет
    return generate_ticket(name=context['name'], email=context['email'])
