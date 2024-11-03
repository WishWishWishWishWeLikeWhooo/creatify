# app/utils/text_generation.py
import openai
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Установка API ключа OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_text(keywords, tone, length, temperature=0.7, max_tokens=150):
    prompt = f"Generate a {tone} text about {keywords} with a length of {length} words."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Или используйте более новую модель, если доступна
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        generated_content = response.choices[0].message['content'].strip()
        logger.info(f"Generated text: {generated_content}")
        return generated_content
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None
