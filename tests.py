from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from vk_api.bot_longpoll import VkBotMessageEvent, VkBotEvent

import settings
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
        # код ниже нужен для того, чтобы переопределить метод listen (bot85). Нужно заменить объект long_poller (bot75)
        # определить у него метод listen и сделать так чтобы он возвращал какой-нибудь список , т.к. listen является
        # генератором и вовзращает список event

        # сколько раз мы вернем наш event, примерное значение
        count = 5
        # создадим любой словарь, оторый будет служить заменой реальным событиям (event, сообщениям от пользователей)
        obj = {'a': 1}
        # создадим список словарей, типа проверим несколько событий в данном случае, как будто нам написали 5 пользоват.
        events = [obj] * count  # [obj, obj, obj, obj, obj]
        # это замена long_poller (bot75) на мок, который будет возвращать список ивентов
        # и работать в bot.on_event = Mock()
        long_poller_mock = Mock(return_value=events)
        # поскольку только метод .listen возвращает нам список, его тоже нужно заменить на мок
        long_poller_listen_mock = Mock()
        # вызываем метод .listen у мока и присваеваем ему другой объект мок, который уже возвращает нам event
        long_poller_listen_mock.listen = long_poller_mock

        # функция патч принимает объект, который ей нужно пропатчить, т.е. заменить на мок объект, чтобы они
        # не вызывались в реальности. Патчи работают с помощью фунции with. Объект api (bot77) тоже стал моком,
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

    INPUTS = [
        # ожидаемые ответы на входе, которые соответсвуют по порядку ответам на выходе из EXPECTED_OUTPUTS
        'Привет',
        'А когда?',
        'Где будет конференция',
        'Зарегистрируй меня',
        'Дмитрий',
        'Мой адрес email@email',
        'email@email.ru'
    ]
    EXPECTED_OUTPUTS = [
        # ожидаемые ответы на выходе, которые соответвуют по порядку ответам на входе из INPUTS
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['registration']['steps']['step1']['text'],
        settings.SCENARIOS['registration']['steps']['step2']['text'],
        settings.SCENARIOS['registration']['steps']['step2']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step3']['text'].format(name='Дмитрий', email='email@email.ru')
    ]

    def test_run_ok(self):
        # создадим мок который нам заменит все входящие event
        send_mock = Mock()
        api_mock = Mock()
        # если кто-то захочет у api (который уже мок) вызвать методы .messages.send то он наткнется на другой мок
        api_mock.message.send = send_mock

        events = []
        for input_text in self.INPUTS:
            # будем подставлять события из INPUTS в RAW_EVENT, но только с помощью deepcopy, т.к если мы изменим в
            # RAW_EVENT наш text у нас не создастся новый класс RAW_EVENT, а изменится тот же самый в итоге мы получим
            # в events = [] несколько одинаковых RAW_EVENT с текстом из последнего события INPUTS 'email@email.ru'.
            # А должны быть RAW_EVENT на каждое событие из INPUTS и на 'Привет' и на 'А когда?' и т.д.
            # deepcopy возвращает полную копию объекта в которую мы уже можем вносить изменения, а именно поменять text.
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            # создаем события
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            # создали объект от класса бот с пустыми параметрами (без group id и token)
            bot = Bot('', '')
            # bot.api тоже будет моком
            bot.api = api_mock
            # bot.on_event = Mock() # коментить
            bot.run()

        print(len(self.INPUTS))
        print(send_mock.call_count)
        # print(bot.on_event.call_count) # коментить
        # проверяем что функция send внутри функции on_event запускалась столько раз сколько у нас INPUTS
        assert send_mock.call_count == len(self.INPUTS)
        # assert bot.on_event.call_count == len(self.INPUTS) # коментить


        # а также мы пробегаемся по листу всех аргументов всех вызовов (столько раз, сколько запускалась функция
        # on_event, т.е. количество INPUTS) и далее на каждом шаге вписываем какие ответы были даны роботом,
        # если они все совпадают с EXPECTED_OUTPUTS то тест пройден
        real_outputs = []
        for call in send_mock.call_args_list: # send_mock.call_args_list/bot.on_event.call_args_list
            args, kwargs = call
            real_outputs.append(kwargs['message'])

        print(real_outputs)
        assert real_outputs == self.EXPECTED_OUTPUTS

    # # Этот тест работал до того, как мы в код добавили работу со сценариями, но сейчас этот тест не работает,
    # т.к. в on_even у нас используется контекст
    # def test_on_event(self):
    #     # только в случае если класс не делает никаких вызовов во вне (только метод __init__)
    #     event = VkBotMessageEvent(raw=self.RAW_EVENT)
    #
    #     # создадим мок который нам заменит все входящие event
    #     send_mock = Mock()
    #
    #     # снова патчим объекты bot.vk_api.VkApi и bot.VkBotLongPoll
    #     with patch('bot.vk_api.VkApi'):
    #         with patch('bot.VkBotLongPoll'):
    #             # создали объект от класса бот с пустыми параметрами (без group id и token)
    #             bot = Bot('', '')
    #             # bot.api тоже будет моком
    #             bot.api = Mock()
    #             # если кто-то захочет у bot.api (который уже мок) вызвать методы .messages.send то он
    #             # наткнется на другой мок
    #             bot.api.messages.send = send_mock
    #
    #             # вызовем метод on_event который принимает вполне реальный event из примера
    #             bot.on_event(event)
    #
    #     # проверим что событие было вызвано лишь один раз и с теми параметрами которые мы ожидаем (bot84)
    #     send_mock.assert_called_once_with(
    #         message=self.RAW_EVENT['object']['message']['text'],
    #         random_id=ANY,
    #         peer_id=self.RAW_EVENT['object']['message']['peer_id'])

# для того чтобы посчитать покрытие кода тестами (т.е. сколько строк из кода были реально исполенны)
# используется утилита coverage (pip install coverage). В консоли запускаем тесты с утилитой coverage:
# coverage run --source=bot -m unittest. Смотреть покрытие тестами только файл bot. Этот вызов создаст файл coverage
# Далее смотрим отчет: coverage report -m.
