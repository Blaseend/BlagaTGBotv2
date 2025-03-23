import json
import os
from bot.utils.errors import send_error_message
from bot.config import USER_CHAT_ID

async def load_data():
    try:
        if os.path.exists('employees_data.json'):
            with open('employees_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"managers": []}
    except Exception as e:
        print(f"Ошибка загрузки данных: {str(e)}")
        return {"managers": []}

async def save_data(data):
    try:
        with open('employees_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Ошибка сохранения данных: {str(e)}")
        return False

def load_sent_links():
    try:
        if os.path.exists('sent_links.json'):
            with open('sent_links.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"sent_links": []}
    except Exception as e:
        print(f"Ошибка загрузки sent_links: {e}")
        return {"sent_links": []}

def save_sent_links(sent_links):
    try:
        with open('sent_links.json', 'w', encoding='utf-8') as f:
            json.dump(sent_links, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения sent_links: {e}")