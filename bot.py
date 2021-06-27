#!/usr/bin/env python3.9

import logging
import random
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
try:
    import settings
except ImportError:
    exit('DO cp settings.py.default settings.py and set token')

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler('bot.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%d-%m-%Y %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)

    log.setLevel(logging.DEBUG)


class Bot:
    """
    Echo bot for vk.com
    Use Python3.9
    """
    def __init__(self, GROUP_ID, TOKEN):
        """
        :param GROUP_ID: group id from vk group
        :param TOKEN: secret token from vk group
        """
        self.group_id = GROUP_ID
        self.token = TOKEN
        self.vk = vk_api.VkApi(token=TOKEN)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """ Run bot """
        for event in self.long_poller.listen():
            # print('Новое сообщение:')
            try:
                self.on_event(event)
            except Exception:
                log.exception('Ошибка в обработке события')

    def on_event(self, event):
        """
        Return message if it's text
        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.debug('Отправляем сообщение назад')
            # print('Текст:', event.message.text)
            self.api.messages.send(message=event.message.text,
                                   random_id=random.randint(0, 2 ** 20),
                                   peer_id=event.message.peer_id)
        else:
            log.info('Пока не умеем обрабатывать события такого типа %s', event.type)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
