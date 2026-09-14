from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_category = State()


class ContactStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_service = State()
    waiting_for_requirement = State()


class AdminStates(StatesGroup):
    waiting_for_update_title = State()
    waiting_for_update_content = State()


class AIStates(StatesGroup):
    chatting = State()