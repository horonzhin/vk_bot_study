from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = 'files/ticket_base.jpeg'
FONT_PATH = 'files/Comfortaa-Regular.ttf'
FONT_SIZE = 20
BLACK = (0, 0, 0, 255)
NAME_OFFSET = (230, 165)
EMAIL_OFFSET = (230, 200)


def generate_ticket(name, email):
    with Image.open(TEMPLATE_PATH).convert("RGBA") as base:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        draw = ImageDraw.Draw(base)
        draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
        draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)

        base.show()
