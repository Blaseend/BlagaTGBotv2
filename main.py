# main.py
import signal
import sys
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from bot.config import API_TOKEN, GROUP_CHAT_ID, USER_CHAT_ID
from bot.handlers import (
    register_managers_handlers,
    register_employees_handlers,
    register_actions_handlers,
    register_cancel_handlers
)
from bot.services.parser import schedule_parsing
from bot.utils.errors import send_shutdown_message, send_error_message

# Глобальная переменная для хранения задачи парсинга
parsing_task = None

async def on_startup(dp: Dispatcher):
    global parsing_task
    await send_startup_message(dp.bot)
    parsing_task = asyncio.create_task(schedule_parsing(dp.bot))

async def send_startup_message(bot: Bot):
    try:
        file_id = "CAACAgIAAxkBAAICemcb4CRF3xph4u6El4k_q2T_Er6zAAJCRAACMTNJS2iiZaxSRU60NgQ"
        await bot.send_sticker(GROUP_CHAT_ID, file_id)
    except Exception as e:
        print(f"Ошибка запуска: {e}")

async def graceful_shutdown(bot: Bot):
    global parsing_task
    
    # Отменяем задачу парсинга
    if parsing_task and not parsing_task.done():
        parsing_task.cancel()
        try:
            await parsing_task
        except asyncio.CancelledError:
            pass

    try:
        # Отправляем сообщение с таймаутом
        await asyncio.wait_for(
            send_shutdown_message(bot, "Корректное завершение работы"),
            timeout=3.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        print(f"Ошибка завершения: {type(e).__name__} - {str(e)}")
    
    # Закрываем соединения
    try:
        session = await bot.get_session()
        await session.close()
    except Exception as e:
        print(f"Ошибка закрытия сессии: {e}")

def handle_exit(signal_received, frame):
    # Получаем текущий event loop
    loop = asyncio.get_event_loop()
    
    # Создаем задачу для graceful shutdown
    shutdown_task = loop.create_task(graceful_shutdown(bot))
    
    # Дожидаемся завершения задачи
    try:
        loop.run_until_complete(shutdown_task)
    except KeyboardInterrupt:
        pass  # Игнорируем повторное нажатие Ctrl+C
    finally:
        sys.exit(0)

if __name__ == '__main__':
    # Инициализация бота
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Регистрация обработчиков
    register_managers_handlers(dp)
    register_employees_handlers(dp)
    register_actions_handlers(dp)
    register_cancel_handlers(dp)

    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    print("⚡️ Бот запущен. Ожидаем событий...")
    
    try:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    finally:
        # Гарантированное закрытие при любом сценарии
        asyncio.run(graceful_shutdown(bot))