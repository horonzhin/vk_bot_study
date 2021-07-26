from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot


class Test1(TestCase):
    # пишем в сообществе вк любое сообщение смотрим, что приходит нам на консоль и тупо копируем все в переменную,
    # как пример того, что мы должны получать
    RAW_EVENT = {
        'type': 'message_new', 'object':
            {'message': {'date': 1624796253, 'from_id': 6218474, 'id': 116, 'out': 0, 'peer_id': 6218474, 'text': 'тм',
                         'conversation_message_id': 113, 'fwd_messages': [], 'important': False, 'random_id': 0,
                         'attachments': [], 'is_hidden': False},
             'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                                'intent_subscribe', 'intent_unsubscribe'], 'keyboard': True,
                             'inline_keyboard': True,
                             'carousel': True, 'lang_id': 0}},
        'group_id': 205318557, 'event_id': '1d104ee315dc2c2d2ca1322b8aec6b3daf8e1f47'}

    def test_run(self):
        # код ниже нужен для того, чтобы переопределить метод listen (bot61). Нужно заменить объект long_poller (bot52)
        # определить у него метод listen и сделать так чтобы он возвращал какой-нибудь список , т.к. listen является
        # генератором и вовзращает список event

        # сколько раз мы вернем наш event, примерное значение
        count = 5
        # создадим любой словарь, оторый будет служить заменой реальным событиям (event, сообщениям от пользователей)
        obj = {'a': 1}
        # создадим список словарей, типа проверим несколько событий в данном случае, как будто нам написали 5 пользоват.
        events = [obj] * count  # [obj, obj, obj, obj, obj]
        # это замена long_poller (bot52) на мок, который будет возвращать список ивентов
        # и работать в bot.on_event = Mock()
        long_poller_mock = Mock(return_value=events)
        # поскольку только метод .listen возвращает нам список, его тоже нужно заменить на мок
        long_poller_listen_mock = Mock()
        # вызываем метод .listen у мока и присваеваем ему другой объект мок, который уже возвращает нам event
        long_poller_listen_mock.listen = long_poller_mock

        # функция патч принимает объект, который ей нужно пропатчить, т.е. заменить на мок объект, чтобы они
        # не вызывались в реальности. Патчи работают с помощью фунции with. Объект api (bot56) тоже стал моком,
        # т.к. вызывался от vk_api.VkApi его не надо отдельно патчить.
        with patch('bot.vk_api.VkApi'):
            # return_value забирает у класса VkBotLongPoll значение и меняет его на новое, т.е. говорит ему
            # что VkBotLongPoll теперь будет long_poller_listen_mock
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                # создали объект от класса бот с пустыми параметрами (без group id и token)
                bot = Bot('', '')
                # по скольку в методе run вызывается метод on_event мы его заменим на мок объект,
                # т.к. в нем может быть куча зависемостей, вызовов и т.д.
                bot.on_event = Mock()
                # запускаем метод run у класса bot чтобы проверит, что он работает
                bot.run()

                # проверяет был ли вообще вызван метод on_event
                bot.on_event.assert_called()
                # убедиться что вызов который был сделан, он сделан с помощью нашего объекта, события, event
                bot.on_event.assert_any_call(obj)
                # проверка что вызов on_event происходил именно с нашими событиями (event) и столько раз сколько надо,
                # в данном случае 5 раз
                assert bot.on_event.call_count == count

    def test_on_event(self):
        # только в случае если класс не делает никаких вызовов во вне (только метод __init__)
        event = VkBotMessageEvent(raw=self.RAW_EVENT)

        # создадим мок который нам заменит все входящие event
        send_mock = Mock()

        # снова патчим объекты bot.vk_api.VkApi и bot.VkBotLongPoll
        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                # создали объект от класса бот с пустыми параметрами (без group id и token)
                bot = Bot('', '')
                # bot.api тоже будет моком
                bot.api = Mock()
                # если кто-то захочет у bot.api (который уже мок) вызвать методы .messages.send то он
                # наткнется на другой мок
                bot.api.messages.send = send_mock

                # вызовем метод on_event который принимает вполне реальный event из примера
                bot.on_event(event)

        # проверим что событие было вызвано лишь один раз и с теми параметрами которые мы ожидаем (bot84)
        send_mock.assert_called_once_with(
            message=self.RAW_EVENT['object']['message']['text'],
            random_id=ANY,
            peer_id=self.RAW_EVENT['object']['message']['peer_id'])

# для того чтобы посчитать покрытие кода тестами (т.е. сколько строк из кода были реально исполенны)
# используется утилита coverage (pip install coverage). В консоли запускаем тесты с утилитой coverage:
# coverage run --source=bot -m unittest. Смотреть покрытие тестами только файл bot. Этот вызов создаст файл coverage
# Далее смотрим отчет: coverage report -m.
