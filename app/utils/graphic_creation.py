# app/utils/graphic_creation.py
import os
import uuid
from PIL import Image, ImageDraw, ImageFont
from flask import current_app


def create_graphic(template, text):
    try:
        # Путь к шаблонам графики
        templates_dir = os.path.join(current_app.root_path, 'static', 'templates_graphics')
        template_path = os.path.join(templates_dir, template)

        # Открытие шаблона
        image = Image.open(template_path).convert('RGBA')
        draw = ImageDraw.Draw(image)

        # Настройка шрифта
        font_path = os.path.join(current_app.root_path, 'static', 'fonts',
                                 'Arial.ttf')  # Убедитесь, что шрифт существует
        font = ImageFont.truetype(font_path, 40)

        # Добавление текста
        text_position = (50, 50)  # Настройте позицию
        text_color = (255, 255, 255, 255)
        draw.text(text_position, text, font=font, fill=text_color)

        # Сохранение созданной графики
        output_filename = f"graphic_{uuid.uuid4().hex}.png"
        output_path = os.path.join(current_app.root_path, 'static', 'graphics', output_filename)

        # Убедитесь, что директория существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        image.save(output_path)

        return output_filename
    except Exception as e:
        current_app.logger.error(f"Error creating graphic: {e}")
        return None
