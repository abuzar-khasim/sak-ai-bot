from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import category_keyboard, main_menu_keyboard
from app.bot.states import ContactStates, RegistrationStates
from app.database.database import AsyncSessionLocal
from app.database.repositories import  create_user, get_user, get_user
from app.services.email_service import send_lead_email


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        existing_user = await get_user(session, telegram_id)

    if existing_user:
        await message.answer(
            f"Welcome back, {existing_user.name}! 👋\n\n"
            "What would you like to do?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(RegistrationStates.waiting_for_name)

    await message.answer(
        "👋 Welcome to SAK AI!\n\n"
        "SAK AI builds AI solutions, intelligent automations, "
        "and AI agents to help you work smarter and automate tasks.\n\n"
        "Let's get to know you first.\n\n"
        "What is your name?"
    )


@router.message(RegistrationStates.waiting_for_name)
async def name_handler(message: Message, state: FSMContext):
    name = (message.text or "").strip()

    if len(name) < 2:
        await message.answer("Please enter a valid name.")
        return

    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_age)

    await message.answer(
        "Nice to meet you! 👋\n\n"
        "How old are you?"
    )


@router.message(RegistrationStates.waiting_for_age)
async def age_handler(message: Message, state: FSMContext):
    try:
        age = int((message.text or "").strip())
    except ValueError:
        await message.answer(
            "Please enter your age as a number.\n\n"
            "Example: 21"
        )
        return

    if age < 5 or age > 120:
        await message.answer("Please enter a valid age.")
        return

    await state.update_data(age=age)
    await state.set_state(RegistrationStates.waiting_for_category)

    await message.answer(
        "Which category describes you best?",
        reply_markup=category_keyboard(),
    )


@router.message(RegistrationStates.waiting_for_category)
async def category_handler(message: Message, state: FSMContext):
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


@router.message(F.text == "🚀 About SAK AI")
async def about_sak_ai_handler(message: Message):
    await message.answer(
        "🤖 About SAK AI\n\n"
        "SAK AI builds intelligent AI solutions, "
        "automations, and AI agents.\n\n"
        "🚀 What we do:\n"
        "• 🤖 AI Solutions\n"
        "• ⚡ Intelligent Automations\n"
        "• 🧠 AI Agents\n"
        "• 🔗 AI-powered Workflows & Integrations\n\n"
        "Our goal is simple — use AI to automate repetitive "
        "work, improve productivity, and solve real-world problems.\n\n"
        "💡 SAK AI — AI • Automations • Agents"
    )


@router.message(F.text == "📩 Contact Us")
async def contact_us_handler(
    message: Message,
    state: FSMContext,
):
    await state.set_state(
        ContactStates.waiting_for_email
    )

    await message.answer(
        "📩 Contact SAK AI\n\n"
        "Let's understand how we can help you.\n\n"
        "Please enter your email address:"
    )


@router.message(ContactStates.waiting_for_email)
async def contact_email_handler(
    message: Message,
    state: FSMContext,
):
    email = (message.text or "").strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        await message.answer(
            "Please enter a valid email address.\n\n"
            "Example: you@example.com"
        )
        return

    await state.update_data(
        email=email
    )

    await state.set_state(
        ContactStates.waiting_for_service
    )

    await message.answer(
        "What are you interested in?\n\n"
        "🤖 AI Solutions\n"
        "⚡ Automations\n"
        "🧠 AI Agents\n"
        "🔗 AI Integrations\n"
        "💡 Other"
    )


@router.message(ContactStates.waiting_for_service)
async def contact_service_handler(
    message: Message,
    state: FSMContext,
):
    service = (message.text or "").strip()

    if not service:
        await message.answer(
            "Please tell us which service you are interested in."
        )
        return

    await state.update_data(
        service=service
    )

    await state.set_state(
        ContactStates.waiting_for_requirement
    )

    await message.answer(
        "Please describe your requirement.\n\n"
        "Tell us what you want to build, automate, "
        "or solve."
    )


@router.message(ContactStates.waiting_for_requirement)
async def contact_requirement_handler(
    message: Message,
    state: FSMContext,
):
    requirement = (message.text or "").strip()
    print(
    f"🧪 REQUIREMENT DEBUG: "
    f"text={message.text!r}, "
    f"length={len(requirement)}, "
    f"state={await state.get_state()}"
)

    if len(requirement) < 5:
        await message.answer(
            "Please provide a little more detail about your requirement."
        )
        return

    data = await state.get_data()

    telegram_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        user = await get_user(
            session,
            telegram_id,
        )

        if not user:
            await state.clear()

            await message.answer(
                "Your account could not be found. "
                "Please use /start first."
            )
            return

        lead = await create_lead(
            session=session,
            telegram_id=telegram_id,
            name=user.name,
            email=data["email"],
            service=data["service"],
            requirement=requirement,
        )

        await state.clear()

    try:
        await send_lead_email(
            name=user.name,
            email=data["email"],
            service=data["service"],
            requirement=requirement,
        )
    except Exception as e:
        print(f"❌ Failed to send lead email: {e}")

    await message.answer(
        "✅ Requirement submitted successfully!\n\n"
    )