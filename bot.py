#!/usr/bin/env python3.9

import logging
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import handlers

try:
    import settings
except ImportError:
    # если программист забудет скопировать сеттингс в сеттингсдефолт мы закроем программу и напишем ему об этом
    exit('DO cp settings.py.default settings.py and set token')

# создаем логгер bot, как отдельный объект логирования
log = logging.getLogger('bot')


def configure_logging():
    # позволяет выводит логеры на консоль (без записи в файл)
    stream_handler = logging.StreamHandler()
    # формат вывода сообщений "уровень - сообщение"
    stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    # установим уровень логирования. От какого уровня выводить сообщения.
    stream_handler.setLevel(logging.INFO)
    # применяем stream_handler к нашему логеру bot
    log.addHandler(stream_handler)

    # позволяет записывать логи в файл
    file_handler = logging.FileHandler('bot.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%d-%m-%Y %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    # по умолчанию уровень логирования error, чтобы наши хэндлеры с info и debug попадали куда нужно укажем общий ур-нь
    log.setLevel(logging.DEBUG)


# класс отвечающий за находение пользователя на каком-то шаге какого-то сценария
class UserState:
    """Состояние пользователя внутри сценария"""

    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        # если контекст пустой (None или пустой Dict) то передадим пустой Dict
        self.context = context or {}


# создаем в вк сообщество. В настройках создаем ключ (токен) и включаем LongPoll.
# В LongPoll включаем нужные события, которые хотим получать.
class Bot:
    """
    Echo bot for vk.com
    Use Python3.9
    Поддерживает ответы на впоросы про дату, место проведения и сценарии регистрации:
    - спрашиваем имя
    - спрашиваем email
    - говорим об успешной регистрации
    Если шаг не пройден, задаем уточняющий вопрос пока шаг не будет пройден
    """

    def __init__(self, GROUP_ID, TOKEN):
        """
        :param GROUP_ID: group id from vk group
        :param TOKEN: secret token from vk group
        """
        self.group_id = GROUP_ID
        self.token = TOKEN
        self.vk = vk_api.VkApi(token=TOKEN)
        # существует либо LongPoll (бот спрашивает есть новые события или нет, через определенное время задержки
        # приходит ответ о том, что есть новые события или нет) либо Callback (присылает уведомления, как только
        # происходит какое-то событие)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        # мотод который позволит боту отвечать пользователю, а не нам
        self.api = self.vk.get_api()
        # переменная отвечающая за состояние пользователя: находение пользователя на каком-то шаге какого-то сценария.
        # Тут есть баг, что если программу перезапустить все стейты сотрутся (имена и почты),
        # чтобы этого не было нужно использовать базы данных
        self.user_states = dict()  # user_id -> UserState

    def run(self):
        """ Run bot """
        for event in self.long_poller.listen():
            # метод listen это бесконечный цикл опрашивания вк на предмет совершения событий. listen это итератор
            # по-этому по нему можно проходить циклом.
            # print('Новое сообщение:') проверочный принт
            try:
                self.on_event(event)
            except Exception:
                # метод exception логирует ошибку с уровнем error, но помимо сообщения будет
                # добавлена подробная информация исключения
                log.exception('Ошибка в обработке события')

    def on_event(self, event):
        """
        Return message if it's text
        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Пока не умеем обрабатывать события такого типа %s', event.type)
            return

        user_id = event.message.peer_id
        text = event.message.text
        # если пользователь в структуре user_states, то продолжаем сценарий, если нет то он вне сценария.
        # Нужно найти интент, чтобы выдать сразу ответ, либо начать сценарий
        if user_id in self.user_states:
            text_to_send = self.continue_scenario(user_id=user_id, text=text)
        else:
            # search intent
            for intent in settings.INTENTS:
                # если нашелся хоть один интернт логируем его хотябы в дебаг
                log.debug(f'User gets {intent}')
                # если какой-нибудь токен находится в тексте среди всех токенов, то запускаем интент. При этом приводим
                # текст к нижнему регистру, т.к. в токенах мы писали их с нижней строки.
                if any(token in text.lower() for token in intent['tokens']):
                    # если интент имеет не пустой ответ, значит надо его сообщить и больше ничего не делать,
                    # если нет, то запустить сценарий
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id, intent['scenario'])
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.api.messages.send(message=text_to_send,
                               # выдергиваем из объекта только текст сообщения
                               random_id=random.randint(0, 2 ** 20),
                               # задержка для того, чтобы если одно и тоже сообщение будет отослано несколько
                               # раз подряд, то пользователь увидит только одно сообщение
                               peer_id=user_id) # id позователя, чтобы ответ пришел именно ему

    # метод который будет запускать сценарии
    def start_scenario(self, user_id, scenario_name):
        scenario = settings.SCENARIOS[scenario_name]
        # первый шаг с которого нужно начать
        first_step = scenario['first_step']
        # запускаем этот первый шаг
        step = scenario['steps'][first_step]
        # выдаем текст этого шага и сохраняем state
        text_to_send = step['text']
        self.user_states[user_id] = UserState(scenario_name=scenario, step_name=first_step)

        return text_to_send

    # метод который будет заниматься только продолжение сценария
    def continue_scenario(self, user_id, text):
        # нужно понять на каком шаге он находится, прошел ли он этот шаг и либо оставить его на этом шаге
        # (если не закончил), либо пребросить на следующий.
        state = self.user_states[user_id]
        steps = state.scenario_name['steps']
        step = steps[state.step_name]
        # далее нужно запустить handler. Нужно понять находится ли данный handler в исходном файле handler
        handler = getattr(handlers, step['handler'])
        # сверяем handler с тем что написал пользователь
        if handler(text=text, context=state.context):
            # если True то следующий шаг
            next_step = steps[step['next_step']]
            # после переходна на новый шаг, нужно отправить сообщение из этого шага с контекстом (имя, почта и т.д.)
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                # если у следующего степа есть некс степ, то переходим в него
                state.step_name = step['next_step']
            else:
                # если пользователь закончил сценарий логируем это в инфо, чтобы видеть с какими данными он его закончил
                log.info('Зарегистрирован: {name} - {email}'.format(**state.context))
                # если нет, то заканчиваем сценарий. Т.е. нужно удалить state из хранилища state
                self.user_states.pop(user_id)
        else:
            # если handler не совпал, то остается на текущем шаге и выдать failure_text
            text_to_send = step['failure_text'].format(**state.context)

        return text_to_send

        #     # если событие типа "новое сообщение" то оно нас интересует
        #     log.debug('Отправляем сообщение назад')
        #     # позволит видеть на консоли, как срабатывают разные уровни логирования
        #     # print('Текст:', event.message.text) проверочный принт
        #     # метод позволяет боту отвечать пользователю. Вид ответа который получит пользователь
        #     self.api.messages.send(message=event.message.text,
        #                            # выдергиваем из объекта только текст сообщения
        #                            random_id=random.randint(0, 2 ** 20),
        #                            # задержка для того, чтобы если одно и тоже сообщение будет отослано несколько
        #                            # раз подряд, то пользователь увидит только одно сообщение
        #                            peer_id=event.message.peer_id)
        #                            # id позователя, чтобы ответ пришел именно ему
        # else:
        # log.info('Пока не умеем обрабатывать события такого типа %s', event.type)
        # # если это событие другого типа, которое мы пока не умеем обрабатывать, то логируем это сообщение.
        # # %s позволяет не форматировать сообщения ниже уровня логирования который мы хотим видеть


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
