#!/usr/bin/env python3.9

from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = 'files/ticket_base.jpeg'
FONT_PATH = 'files/Comfortaa-Regular.ttf'
FONT_SIZE = 20
BLACK = (0, 0, 0, 255)
NAME_OFFSET = (230, 165)
EMAIL_OFFSET = (230, 200)
AVATAR_SIZE = 100
AVATAR_OFFSET = (80, 155)


def generate_ticket(name, email):
    with Image.open(TEMPLATE_PATH).convert("RGBA") as base:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        draw = ImageDraw.Draw(base)
        draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
        draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)

        try:
            response = requests.get(url=f'https://bucket.roach.gg/avatars/default/44.png')
            # TODO Чтобы все работало, как задумывалось, нужно найти ресурс генерации аваторок по почте
            #  (любому тексту, в нашем случае почте) с сохранением картини в формате png, jpeg и т.д.
            #  Хотел использовать api.adorable.io, но он больше не работает. url должен бы быть следующим:
            #  https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}
            #  Либо переписать код, чтобы генерация была через какую-нибудь библиотеку.
            avatar_file_like = BytesIO(response.content)
            avatar = Image.open(avatar_file_like)

            base.paste(avatar, AVATAR_OFFSET)
            # base.show()

        except Exception as exc:
            print(f'Сайт не отвечает: {exc}')

        temp_file = BytesIO()
        base.save(temp_file, 'png')
        temp_file.seek(0)

        return temp_file
