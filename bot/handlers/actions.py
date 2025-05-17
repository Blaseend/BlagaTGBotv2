from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.states.form_states import Form
from bot.services.database import load_data, save_data
from bot.utils.logging import debug_log

async def process_action(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    debug_log("Действие", {"action": action})
    
    if action == 'edit':
        await Form.edit_name.set()
        await callback_query.message.edit_text("Введите новое имя сотрудника:")
    elif action == 'delete':
        user_data = await state.get_data()
        data = await load_data()
        manager = next(m for m in data['managers'] if m['telegram_login'] == user_data['selected_manager'])
        manager['employees'] = [e for e in manager['employees'] if e['name'] != user_data['selected_employee']]
        
        if await save_data(data):
            await callback_query.message.edit_text("✅ Сотрудник удалён!")
        await state.finish()
    
    await callback_query.answer()

async def process_edit_name(message: types.Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await Form.edit_master_id.set()
    await message.answer("Введите новый masterID:")

async def process_edit_master_id(message: types.Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        data = await load_data()
        manager = next(m for m in data['managers'] if m['telegram_login'] == user_data['selected_manager'])
        employee = next(e for e in manager['employees'] if e['name'] == user_data['selected_employee'])
        
        employee.update({
            "name": user_data['new_name'],
            "masterID": int(message.text)
        })
        
        if await save_data(data):
            await message.answer("✅ Данные обновлены!")
        await state.finish()
    except ValueError:
        await message.answer("❌ MasterID должен быть числом!")
    except Exception as e:
        await message.answer("❌ Ошибка сохранения")
        debug_log("Ошибка редактирования", {"error": str(e)})
        await state.finish()

def register_actions_handlers(dp):
    dp.register_callback_query_handler(process_action, lambda c: c.data.startswith('action_'), state=Form.select_action)
    dp.register_message_handler(process_edit_name, state=Form.edit_name)
    dp.register_message_handler(process_edit_master_id, state=Form.edit_master_id)