# bot/utils/errors.py
from bot.config import USER_CHAT_ID

async def send_error_message(bot, error_message: str):
    try:
        await bot.send_message(USER_CHAT_ID, f"🚨 Ошибка: {error_message}")
    except Exception as e:
        print(f"Не удалось отправить сообщение об ошибке: {e}")

async def send_shutdown_message(bot, reason: str):
    try:
        await bot.send_message(USER_CHAT_ID, f"🛑 Остановка бота. Причина: {reason}")
    except Exception as e:
        print(f"Ошибка отправки сообщения об остановке: {e}")