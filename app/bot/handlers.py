from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import category_keyboard, main_menu_keyboard
from app.bot.states import ContactStates, RegistrationStates
from app.database.database import AsyncSessionLocal
from app.database.repositories import  create_lead, get_user, get_user, get_published_updates
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
        "🚀 <b>About SAK AI</b>\n\n"
        "<b>SAK AI — AI • Automations • Agents</b>\n\n"
        "We build intelligent AI solutions that help businesses "
        "automate repetitive work, connect their tools, and create "
        "AI-powered workflows.\n\n"
        
        "<b>What we do</b>\n"
        "🤖 AI Solutions\n"
        "⚡ Intelligent Automations\n"
        "🧠 AI Agents\n"
        "🔗 AI Integrations\n\n"
        
        "Our goal is simple:\n"
        "<b>Turn repetitive work into intelligent systems.</b>\n\n"
        
        "💡 Have an idea or business problem?\n"
        "Let's discuss how AI can help.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
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

@router.message(F.text == "📢 Updates")
async def updates_handler(message: Message):
    print("🧪 UPDATES HANDLER CALLED")

    async with AsyncSessionLocal() as session:
        updates = await get_published_updates(session)

    print(f"🧪 UPDATES FOUND: {len(updates)}")

    if not updates:
        await message.answer(
            "📢 <b>SAK AI Updates</b>\n\n"
            "No new updates at the moment.\n\n"
            "Stay tuned! 🚀",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    response = "📢 <b>SAK AI Updates</b>\n\n"

    for update in updates:
        response += (
            f"🚀 <b>{update.title}</b>\n"
            f"{update.content}\n\n"
            "━━━━━━━━━━━━━━\n\n"
        )

    await message.answer(
        response,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
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

        print(
            f"✅ Lead email sent successfully for lead #{lead.id}"
        )

    except Exception as e:
        print(f"❌ Failed to send lead email: {e}")

    await message.answer(
        "✅ Requirement submitted successfully!\n\n"
        f"Reference ID: #{lead.id}\n\n"
        "Our team will review your requirement and "
        "get back to you.\n\n"
        "Thank you for choosing SAK AI. 🤖",
        reply_markup=main_menu_keyboard(),
    )