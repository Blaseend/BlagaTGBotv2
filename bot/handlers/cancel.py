from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.utils.logging import debug_log

async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("Операция отменена")
    await callback_query.answer()

def register_cancel_handlers(dp):
    dp.register_callback_query_handler(cancel_handler, lambda c: c.data == 'cancel', state='*')