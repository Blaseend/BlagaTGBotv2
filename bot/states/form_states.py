from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    select_manager = State()
    select_employee = State()
    select_action = State()
    edit_name = State()
    edit_master_id = State()
    new_employee_name = State()
    new_employee_master_id = State()
    new_manager_login = State()
    confirm_delete_manager = State()
    select_manager_to_delete = State()