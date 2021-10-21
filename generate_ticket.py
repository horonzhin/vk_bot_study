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
            # передаем на вход файловому дискриптору IO (на подобие работы с фалами .open/.write и т.д.) байты
            # (.content),чтобы потом работать с ним, как с обычным файлом. Позволяет записывать данные в память и не
            # хранить их нигде. https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}
            # TODO Чтобы заработало нужно найти ресурс генерации аваторок по почте с сохранением картини в формате png,
            #  jpeg и т.д. api.adorable.io больше не работает. Либо переписать код, чтобы генерация была через
            #  какую-нибудь библиотеку
            avatar_file_like = BytesIO(response.content)
            avatar = Image.open(avatar_file_like)

            base.paste(avatar, AVATAR_OFFSET)
            # base.show()

        except Exception as exc:
            print(f'Сайт не отвечает: {exc}')

        # тоже что код ниже "with open" только ничего не создается и не занимает память. Файловый дискриптор BytesIO
        # хранит только байты, но позволяет работать с ними, как с файлом. Ниже мы использовали "with open", чтобы
        # сохранить пример.
        temp_file = BytesIO()
        base.save(temp_file, 'png')
        # когда байты записались в дискриптор курсор остался в конце строки после всех байтов, чтобы потом можно было
        # прочитать его, курсор нужно вернуть в начальное положение, иначе читающий ничего не увидит.
        temp_file.seek(0)

        return temp_file

        # base.show()
        # открываем какой-нибудь файл для записи и откроем его для записи в виде байт. Не преобразуем никакие тексты
        # ни в каких кодеровках, а пишем чистые байты.
        # with open('files/ticket_example.png', 'wb') as f:
        #     base.save(f, 'png')

