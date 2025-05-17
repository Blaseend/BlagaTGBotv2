from aiogram import types
from aiogram.dispatcher import FSMContext
from bot.states.form_states import Form
from bot.utils.logging import debug_log
from aiogram.dispatcher import FSMContext
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.database import load_data, save_data, load_sent_links, save_sent_links, add_sent_link


PRIVILEGED_USERS = ["@team_lead_ivanov", "@hr_manager"]
PAGE_LIMIT = 5 

async def cmd_start(message: types.Message, state: FSMContext):
    debug_log("Начало работы", {"user": message.from_user.username})
    data = await load_data()
    
    user_name = message.from_user.full_name
    greeting = f"👋 Привет, {user_name}!\n\n"
    manager_login = f"@{message.from_user.username}" if message.from_user.username else None
    is_privileged = message.from_user.username in PRIVILEGED_USERS
    
    # Ищем менеджера (даже для привилегированных пользователей)
    manager = next((m for m in data['managers'] if m['telegram_login'].lower() == manager_login.lower()), None) if manager_login else None
    
    if manager or is_privileged:
        # Основное меню для менеджеров и привилегированных пользователей
        await state.update_data(selected_manager=manager['telegram_login'] if manager else None)
        
        markup = types.InlineKeyboardMarkup()
        
        # Если есть сотрудники - показываем их
        if manager and manager['employees']:
            for employee in manager['employees']:
                safe_name = employee['name'].replace('_', '%%UNDERSCORE%%')
                markup.add(types.InlineKeyboardButton(
                    text=employee['name'],
                    callback_data=f"employee_{safe_name}"
                ))
        
        # Кнопки для всех менеджеров
        buttons = [
            types.InlineKeyboardButton("Добавить сотрудника ➕", callback_data="add_employee"),
            types.InlineKeyboardButton("📊 Статистика", callback_data="show_statistics")
        ]
        
        # Дополнительные кнопки для привилегированных пользователей
        if is_privileged:
            buttons.append(types.InlineKeyboardButton("⚙️ Управление менеджерами", callback_data="manage_managers"))
        
        markup.row(*buttons)
        markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
        
        await Form.select_employee.set()
        message_text = greeting + ("Выбери сотрудника или действие:" if manager else "Доступные действия:")
        await message.answer(message_text, reply_markup=markup)
    else:
        await message.answer(greeting + "❌ У вас нет доступа к этому боту. Обратитесь к администратору.")

async def manage_managers(callback_query: types.CallbackQuery, state: FSMContext):
    """Меню управления менеджерами для привилегированных пользователей"""
    data = await load_data()
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("Добавить менеджера ➕", callback_data="add_manager"),
        types.InlineKeyboardButton("Удалить менеджера ❌", callback_data="delete_manager")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
    
    await callback_query.message.edit_text(
        "⚙️ Управление менеджерами:",
        reply_markup=markup
    )
    await callback_query.answer()

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

async def add_manager(callback_query: types.CallbackQuery):
    await Form.new_manager_login.set()
    await callback_query.message.edit_text("Введите telegram_login нового менеджера:")
    await callback_query.answer()

async def process_new_manager_login(message: types.Message, state: FSMContext):
    try:
        new_login = message.text.strip()
        if not new_login:
            await message.answer("❌ Логин не может быть пустым!")
            return
            
        data = await load_data()
        
        if any(m['telegram_login'].lower() == new_login.lower() for m in data['managers']):
            await message.answer("❌ Менеджер с таким логином уже существует!")
            await state.finish()
            return
        
        data['managers'].append({
            "telegram_login": new_login,
            "employees": []
        })
        
        if await save_data(data):
            await message.answer(f"✅ Менеджер {new_login} успешно добавлен!")
        await state.finish()
        
        await cmd_start(message)
    except Exception as e:
        await message.answer("❌ Ошибка при сохранении данных")
        debug_log("Ошибка добавления менеджера", {"error": str(e)})
        await state.finish()

async def delete_manager(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data = await load_data()
        if not data['managers']:
            await callback_query.message.edit_text("Нет менеджеров для удаления")
            await callback_query.answer()
            return

        markup = types.InlineKeyboardMarkup()
        for manager in data['managers']:
            safe_login = manager['telegram_login'].replace('_', '%%UNDERSCORE%%')
            markup.add(types.InlineKeyboardButton(
                text=manager['telegram_login'],
                callback_data=f"delete_manager_{safe_login}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
        
        await Form.select_manager_to_delete.set()
        await callback_query.message.edit_text(
            "Выберите менеджера для удаления:",
            reply_markup=markup
        )
    except Exception as e:
        debug_log("Ошибка в delete_manager", {"error": str(e)})
        await callback_query.message.edit_text("❌ Произошла ошибка при выборе менеджера")
    await callback_query.answer()

async def confirm_delete_manager(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        # Изменяем обработку callback_data
        safe_login = callback_query.data.split('delete_manager_')[1]
        manager_login = safe_login.replace('%%UNDERSCORE%%', '_')
        
        # Сохраняем выбранного менеджера в state
        await state.update_data(manager_to_delete=manager_login)
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Да, удалить", callback_data="confirm_delete_yes"),
            types.InlineKeyboardButton("❌ Нет, отмена", callback_data="back_to_start")
        )
        
        await Form.confirm_delete_manager.set()
        await callback_query.message.edit_text(
            f"Вы уверены, что хотите удалить менеджера {manager_login} и всех его сотрудников?",
            reply_markup=markup
        )
    except Exception as e:
        debug_log("Ошибка в confirm_delete_manager", {"error": str(e)})
        await callback_query.message.edit_text("❌ Ошибка при подтверждении удаления")
    await callback_query.answer()

async def execute_delete_manager(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        manager_login = user_data.get('manager_to_delete')
        
        if not manager_login:
            await callback_query.message.edit_text("❌ Не удалось определить менеджера для удаления")
            await state.finish()
            return
        
        data = await load_data()
        initial_count = len(data['managers'])
        data['managers'] = [m for m in data['managers'] if m['telegram_login'] != manager_login]
        
        if len(data['managers']) < initial_count:
            if await save_data(data):
                await callback_query.message.edit_text(f"✅ Менеджер {manager_login} и его сотрудники успешно удалены!")
            else:
                await callback_query.message.edit_text("❌ Ошибка при сохранении данных")
        else:
            await callback_query.message.edit_text(f"❌ Менеджер {manager_login} не найден")
        
        await state.finish()
        # Возвращаем пользователя в главное меню
        await cmd_start(await callback_query.message.answer("Меню обновлено:"))
    except Exception as e:
        debug_log("Ошибка в execute_delete_manager", {"error": str(e)})
        await callback_query.message.edit_text("❌ Ошибка при удалении менеджера")
    await callback_query.answer()

async def show_statistics(callback_query: types.CallbackQuery, state: FSMContext, page=0):
    try:
        user_data = await state.get_data()
        manager_login = user_data.get('selected_manager')
        sent_links = load_sent_links()

        # Фильтрация по менеджеру
        manager_links = [
            link for link in sent_links['sent_links']
            if link['manager_login'].lower() == manager_login.lower()
        ]

        if not manager_links:
            await callback_query.message.edit_text("У вас пока нет полученных ссылок.")
            return

        # Группировка по дате и master_id
        grouped = {}
        for link in manager_links:
            try:
                date = datetime.fromisoformat(link['date']).strftime('%d.%m.%y')
            except Exception:
                continue  # Пропускаем некорректную дату
            master_id = link['master_id']
            if date not in grouped:
                grouped[date] = {}
            if master_id not in grouped[date]:
                grouped[date][master_id] = []
            grouped[date][master_id].append(link)

        # Пагинация
        all_dates = sorted(grouped.keys(), reverse=True)
        total_pages = (len(all_dates) + PAGE_LIMIT - 1) // PAGE_LIMIT
        current_dates = all_dates[page*PAGE_LIMIT:(page+1)*PAGE_LIMIT]

        # Формирование сообщения
        message = f"📊 Ваша статистика (стр. {page+1}/{total_pages}):\n\n"
        for date in current_dates:
            message += f"<b>{date}</b>\n"
            for master_id, links in grouped[date].items():
                employee_name = links[0]['employee_name']
                message += f"\nMaster ID: {master_id} ({employee_name})\n"
                for link in links:
                    message += f"- {link['url']}\n"
            message += "\n"

        # Клавиатура
        markup = InlineKeyboardMarkup()
        if len(all_dates) > PAGE_LIMIT:
            row = []
            if page > 0:
                row.append(InlineKeyboardButton("⬅️", callback_data=f"stats_page_{page-1}"))
            if page < total_pages - 1:
                row.append(InlineKeyboardButton("➡️", callback_data=f"stats_page_{page+1}"))
            markup.row(*row)

        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_employees"))

        await callback_query.message.edit_text(message, reply_markup=markup)
        await callback_query.answer()

    except Exception as e:
        await callback_query.answer("Произошла ошибка при загрузке статистики")
        debug_log("Ошибка в show_statistics", {"error": str(e)})
       
# Добавим обработчик для back_to_employees
async def back_to_employees_handler(callback_query: types.CallbackQuery, state: FSMContext):
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
            types.InlineKeyboardButton("📊 Статистика", callback_data="show_statistics")
        )
        markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
        
        await Form.select_employee.set()
        await callback_query.message.edit_text(
            "Выбери существующего сотрудника или добавь нового:",
            reply_markup=markup
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("Произошла ошибка")
        debug_log("Ошибка в back_to_employees_handler", {"error": str(e)})

async def handle_stats_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[-1])
    await show_statistics(callback_query, state, page)



def register_managers_handlers(dp):
    dp.register_message_handler(cmd_start, commands=['start'], state='*')
    dp.register_callback_query_handler(process_manager, lambda c: c.data.startswith('manager_'), state=Form.select_manager)
    dp.register_callback_query_handler(back_to_start, lambda c: c.data == 'back_to_start', state='*')
    
    dp.register_callback_query_handler(add_manager, lambda c: c.data == 'add_manager', state='*')  # Было Form.select_manager
    dp.register_message_handler(process_new_manager_login, state=Form.new_manager_login)
    dp.register_callback_query_handler(delete_manager, lambda c: c.data == 'delete_manager', state='*')  # Было Form.select_manager
    dp.register_callback_query_handler(confirm_delete_manager, lambda c: c.data.startswith('delete_manager_'), state='*')  # Было Form.select_manager_to_delete
    dp.register_callback_query_handler(execute_delete_manager, lambda c: c.data == 'confirm_delete_yes', state='*')  # Было Form.confirm_delete_manager
    
    dp.register_callback_query_handler(show_statistics, lambda c: c.data == 'show_statistics', state=Form.select_employee)
    dp.register_callback_query_handler(handle_stats_pagination, lambda c: c.data.startswith('stats_page_'), state=Form.select_employee)
    dp.register_callback_query_handler(back_to_employees_handler, lambda c: c.data == 'back_to_employees', state='*')
    dp.register_callback_query_handler(manage_managers, lambda c: c.data == 'manage_managers', state='*')