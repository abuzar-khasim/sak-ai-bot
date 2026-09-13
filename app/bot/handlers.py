from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import (
    category_keyboard,
    main_menu_keyboard,
)
from app.bot.states import RegistrationStates
from app.database.database import AsyncSessionLocal
from app.database.repositories import (
    create_user,
    get_user,
)


router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    telegram_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        existing_user = await get_user(
            session,
            telegram_id,
        )

    if existing_user:
        await message.answer(
            f"Welcome back, {existing_user.name}! 👋\n\n"
            "What would you like to do?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(
        RegistrationStates.waiting_for_name
    )

    await message.answer(
        "👋 Welcome to SAK AI!\n\n"
        "SAK AI provides AI, Automation and "
        "Software Development services.\n\n"
        "Let's get to know you first.\n\n"
        "What is your name?"
    )


@router.message(RegistrationStates.waiting_for_name)
async def name_handler(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if len(name) < 2:
        await message.answer(
            "Please enter a valid name."
        )
        return

    await state.update_data(name=name)

    await state.set_state(
        RegistrationStates.waiting_for_age
    )

    await message.answer(
        "Nice to meet you! 👋\n\n"
        "How old are you?"
    )


@router.message(RegistrationStates.waiting_for_age)
async def age_handler(
    message: Message,
    state: FSMContext,
):
    try:
        age = int((message.text or "").strip())
    except ValueError:
        await message.answer(
            "Please enter your age as a number.\n\n"
            "Example: 21"
        )
        return

    if age < 5 or age > 120:
        await message.answer(
            "Please enter a valid age."
        )
        return

    await state.update_data(age=age)

    await state.set_state(
        RegistrationStates.waiting_for_category
    )

    await message.answer(
        "Which category describes you best?",
        reply_markup=category_keyboard(),
    )


@router.message(
    RegistrationStates.waiting_for_category
)
async def category_handler(
    message: Message,
    state: FSMContext,
):
    category = (message.text or "").strip()

    allowed_categories = {
        "🎓 Student",
        "💼 Working Professional",
        "🏢 Business Owner",
        "🧑‍💻 Freelancer",
        "🔹 Other",
    }

    if category not in allowed_categories:
        await message.answer(
            "Please select one of the options.",
            reply_markup=category_keyboard(),
        )
        return

    data = await state.get_data()

    telegram_id = message.from_user.id
    username = message.from_user.username

    async with AsyncSessionLocal() as session:
        user = await create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            name=data["name"],
            age=data["age"],
            category=category,
        )

    await state.clear()

    await message.answer(
        f"Registration complete, {user.name}! ✅\n\n"
        "Welcome to SAK AI.\n\n"
        "How can we help you?",
        reply_markup=main_menu_keyboard(),
    )