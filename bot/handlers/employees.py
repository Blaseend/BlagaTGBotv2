from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.states.form_states import Form
from bot.services.database import load_data, save_data
from bot.utils.logging import debug_log
from bot.handlers.managers import cmd_start  # Импорт после объявления функций

async def process_employee(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        safe_name = callback_query.data.split('employee_')[1]
        employee_name = safe_name.replace('%%UNDERSCORE%%', '_')
        debug_log("Выбор сотрудника", {"employee": employee_name})
        
        await state.update_data(selected_employee=employee_name)
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Редактировать ✏️", callback_data="action_edit"),
            types.InlineKeyboardButton("Удалить ❌", callback_data="action_delete")
        )
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_employees"))
        
        await Form.select_action.set()
        await callback_query.message.edit_text(
            f"Выбран сотрудник: {employee_name}",
            reply_markup=markup
        )
    except Exception as e:
        debug_log("Ошибка в process_employee", {"error": str(e)})
    await callback_query.answer()

async def back_to_employees(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        manager_login = user_data.get('selected_manager')
        data = await load_data()
        manager = next((m for m in data['managers'] if m['telegram_login'] == manager_login), None)

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
        debug_log("Ошибка в back_to_employees", {"error": str(e)})
    await callback_query.answer()

async def add_employee(callback_query: types.CallbackQuery):
    await Form.new_employee_name.set()
    await callback_query.message.edit_text("Введите имя нового сотрудника:")
    await callback_query.answer()

async def process_new_employee_name(message: types.Message, state: FSMContext):
    await state.update_data(new_employee_name=message.text)
    await Form.new_employee_master_id.set()
    await message.answer("Введите masterID нового сотрудника:")

async def process_new_employee_master_id(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        data = await load_data()
        manager = next(m for m in data['managers'] if m['telegram_login'] == user_data['selected_manager'])
        
        manager['employees'].append({
            "masterID": int(message.text),
            "name": user_data['new_employee_name']
        })
        
        if await save_data(data):
            await message.answer("✅ Сотрудник успешно добавлен!")
        await state.finish()
    except ValueError:
        await message.answer("❌ MasterID должен быть числом!")
        return
    except Exception as e:
        await message.answer("❌ Ошибка при сохранении данных")
        debug_log("Ошибка добавления", {"error": str(e)})
        await state.finish()

def register_employees_handlers(dp):
    dp.register_callback_query_handler(process_employee, lambda c: c.data.startswith('employee_'), state=Form.select_employee)
    dp.register_callback_query_handler(back_to_employees, lambda c: c.data == 'back_to_employees', state=Form.select_action)
    dp.register_callback_query_handler(add_employee, lambda c: c.data == 'add_employee', state=Form.select_employee)
    dp.register_message_handler(process_new_employee_name, state=Form.new_employee_name)
    dp.register_message_handler(process_new_employee_master_id, state=Form.new_employee_master_id)