from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.states.form_states import Form
from bot.services.database import load_data
from bot.utils.logging import debug_log

async def cmd_start(message: types.Message):
    debug_log("Начало работы", {"user": message.from_user.username})
    await Form.select_manager.set()
    data = await load_data()
    
    markup = types.InlineKeyboardMarkup()
    for manager in data['managers']:
        safe_login = manager['telegram_login'].replace('_', '%%UNDERSCORE%%')
        markup.add(types.InlineKeyboardButton(
            text=manager['telegram_login'],
            callback_data=f"manager_{safe_login}"
        ))
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    
    await message.answer("Выбери РГ для редактирования:", reply_markup=markup)

async def process_manager(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        safe_login = callback_query.data.split('manager_')[1]
        manager_login = safe_login.replace('%%UNDERSCORE%%', '_')
        debug_log("Выбор менеджера", {"manager": manager_login})
        
        await state.update_data(selected_manager=manager_login)
        data = await load_data()
        manager = next((m for m in data['managers'] if m['telegram_login'] == manager_login), None)
        
        if not manager:
            await callback_query.answer("Менеджер не найден!")
            return

        markup = types.InlineKeyboardMarkup()
        for employee in manager['employees']:
            safe_name = employee['name'].replace('_', '%%UNDERSCORE%%')
            markup.add(types.InlineKeyboardButton(
                text=employee['name'],
                callback_data=f"employee_{safe_name}"
            ))
        markup.row(
            types.InlineKeyboardButton("Добавить сотрудника ➕", callback_data="add_employee"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")
        )
        
        await Form.select_employee.set()
        await callback_query.message.edit_text(
            "Выбери существующего сотрудника или добавь нового:",
            reply_markup=markup
        )
    except Exception as e:
        debug_log("Ошибка в process_manager", {"error": str(e)})
    await callback_query.answer()

async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await cmd_start(await callback_query.message.answer("Меню обновлено:"))
    await callback_query.answer()

def register_managers_handlers(dp):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_callback_query_handler(process_manager, lambda c: c.data.startswith('manager_'), state=Form.select_manager)
    dp.register_callback_query_handler(back_to_start, lambda c: c.data == 'back_to_start', state='*')