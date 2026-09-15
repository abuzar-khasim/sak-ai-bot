from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.router import LLMRouter
from app.ai.service import AIService
from app.bot.keyboards import (
    admin_keyboard,
    category_keyboard,
    main_menu_keyboard,
    manage_updates_keyboard,
)
from app.bot.states import (
    AdminStates,
    AIStates,
    ContactStates,
    RegistrationStates,
)
from app.config.settings import settings
from app.database.database import AsyncSessionLocal
from app.database.models import Update
from app.database.repositories import (
    create_lead,
    create_user,
    get_published_updates,
    get_user,
)
from app.services.email_service import send_lead_email


router = Router()

router.llm_router: LLMRouter | None = None


def is_admin(telegram_id: int) -> bool:
    return telegram_id == settings.admin_telegram_id


# ============================================================
# START / REGISTRATION
# ============================================================

@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    telegram_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        user = await get_user(
            session=session,
            telegram_id=telegram_id,
        )

    if user:
        await message.answer(
            f"👋 Welcome back, {user.name}!\n\n"
            "How can I help you today?",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(
        RegistrationStates.waiting_for_name
    )

    await message.answer(
        "👋 Welcome to <b>SAK AI</b>!\n\n"
        "I'm your AI assistant for AI solutions, "
        "automations, agents, and intelligent workflows.\n\n"
        "Let's get you started.\n\n"
        "Please enter your name:",
        parse_mode="HTML",
    )


@router.message(
    RegistrationStates.waiting_for_name,
    F.text,
)
async def registration_name_handler(
    message: Message,
    state: FSMContext,
):
    name = message.text.strip()

    if not name:
        await message.answer(
            "Please enter a valid name."
        )
        return

    if len(name) > 255:
        await message.answer(
            "Please enter a shorter name."
        )
        return

    await state.update_data(name=name)

    await state.set_state(
        RegistrationStates.waiting_for_age
    )

    await message.answer(
        "Great! 👍\n\n"
        "Please enter your age:"
    )


@router.message(
    RegistrationStates.waiting_for_age,
    F.text,
)
async def registration_age_handler(
    message: Message,
    state: FSMContext,
):
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer(
            "⚠️ Please enter your age as a number."
        )
        return

    if age < 1 or age > 120:
        await message.answer(
            "⚠️ Please enter a valid age between 1 and 120."
        )
        return

    await state.update_data(age=age)

    await state.set_state(
        RegistrationStates.waiting_for_category
    )

    await message.answer(
        "Almost done! 🎯\n\n"
        "Please select your category:",
        reply_markup=category_keyboard(),
    )


@router.message(
    RegistrationStates.waiting_for_category,
    F.text,
)
async def registration_category_handler(
    message: Message,
    state: FSMContext,
):
    category_map = {
        "🎓 Student": "Student",
        "💼 Working Professional": "Working Professional",
        "🏢 Business Owner": "Business Owner",
        "🧑‍💻 Freelancer": "Freelancer",
        "🔹 Other": "Other",
    }

    category = category_map.get(message.text)

    if category is None:
        await message.answer(
            "Please select one of the available categories.",
            reply_markup=category_keyboard(),
        )
        return

    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        await create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=data["name"],
            age=data["age"],
            category=category,
        )

    await state.clear()

    await message.answer(
        "✅ Registration completed successfully!\n\n"
        f"Welcome to <b>SAK AI</b>, {data['name']}! 🤖\n\n"
        "How can I help you?",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# MAIN MENU
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "🚀 About SAK AI",
)
async def about_sak_ai_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "<b>🤖 SAK AI</b>\n\n"
        "SAK AI — <b>AI • Automations • Agents</b>\n\n"
        "We focus on:\n"
        "• AI Solutions\n"
        "• Intelligent Automations\n"
        "• AI Agents\n"
        "• AI-powered Workflows & Integrations\n\n"
        "Our goal is to make AI practical, useful, "
        "and accessible for individuals and businesses.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# CONTACT US
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "📩 Contact Us",
)
async def contact_us_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await state.set_state(
        ContactStates.waiting_for_email
    )

    await message.answer(
        "📩 <b>Contact SAK AI</b>\n\n"
        "Let's understand your requirement.\n\n"
        "Please enter your email address:",
        parse_mode="HTML",
    )


@router.message(
    ContactStates.waiting_for_email,
    F.text,
)
async def contact_email_handler(
    message: Message,
    state: FSMContext,
):
    email = message.text.strip()

    if "@" not in email or "." not in email:
        await message.answer(
            "⚠️ Please enter a valid email address."
        )
        return

    await state.update_data(email=email)

    await state.set_state(
        ContactStates.waiting_for_service
    )

    await message.answer(
        "What service are you interested in?\n\n"
        "For example:\n"
        "• AI Agent\n"
        "• Automation\n"
        "• AI Integration\n"
        "• Custom AI Solution"
    )


@router.message(
    ContactStates.waiting_for_service,
    F.text,
)
async def contact_service_handler(
    message: Message,
    state: FSMContext,
):
    service = message.text.strip()

    if not service:
        await message.answer(
            "Please enter the service you're interested in."
        )
        return

    await state.update_data(service=service)

    await state.set_state(
        ContactStates.waiting_for_requirement
    )

    await message.answer(
        "Please describe your requirement.\n\n"
        "Tell us what you want to build or automate."
    )


@router.message(
    ContactStates.waiting_for_requirement,
    F.text,
)
async def contact_requirement_handler(
    message: Message,
    state: FSMContext,
):
    requirement = message.text.strip()

    if not requirement:
        await message.answer(
            "Please describe your requirement."
        )
        return

    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        await create_lead(
            session=session,
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            email=data["email"],
            service=data["service"],
            requirement=requirement,
        )

    try:
        await send_lead_email(
            name=message.from_user.full_name,
            email=data["email"],
            service=data["service"],
            requirement=requirement,
        )

        email_status = (
            "Our team has been notified successfully."
        )

    except Exception as error:
        print(
            "❌ Lead email error:",
            type(error).__name__,
            error,
        )

        email_status = (
            "Your requirement was saved successfully. "
            "Our team will review it."
        )

    await state.clear()

    await message.answer(
        "✅ <b>Requirement submitted!</b>\n\n"
        f"{email_status}\n\n"
        "Thank you for contacting SAK AI. 🚀",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# UPDATES — USER
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "📢 Updates",
)
async def updates_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    async with AsyncSessionLocal() as session:
        updates = await get_published_updates(session)

    if not updates:
        await message.answer(
            "📢 <b>SAK AI Updates</b>\n\n"
            "There are currently no updates.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    text = "📢 <b>SAK AI Updates</b>\n\n"

    for update in updates:
        text += (
            f"<b>{update.title}</b>\n"
            f"{update.content}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# ASK SAK AI
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "🔎 Ask SAK AI",
)
async def ask_sak_ai_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    if router.llm_router is None:
        await message.answer(
            "⚠️ AI service is currently unavailable. "
            "Please try again later."
        )
        return

    await state.set_state(
        AIStates.chatting
    )

    await message.answer(
        "🤖 <b>SAK AI</b>\n\n"
        "Ask me anything.\n\n"
        "You can ask me about AI, automations, "
        "agents, technology, business ideas, "
        "coding, or general questions.\n\n"
        "Send your question below.",
        parse_mode="HTML",
    )


@router.message(
    AIStates.chatting,
    F.text,
)
async def ai_chat_handler(
    message: Message,
    state: FSMContext,
):
    if router.llm_router is None:
        await message.answer(
            "⚠️ AI service is currently unavailable."
        )
        return

    user_text = message.text.strip()

    if not user_text:
        return

    try:
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
        )
    except Exception:
        pass

    try:
        async with AsyncSessionLocal() as session:
            ai_service = AIService(
                router.llm_router
            )

            response, model = (
                await ai_service.generate_response(
                    session=session,
                    telegram_id=message.from_user.id,
                    user_message=user_text,
                )
            )

        await message.answer(response)

        print(
            f"🤖 AI response | "
            f"user={message.from_user.id} | "
            f"model={model}"
        )

    except ValueError as error:
        await message.answer(str(error))

    except Exception as error:
        print(
            "❌ AI chat error:",
            type(error).__name__,
            error,
        )

        await message.answer(
            "⚠️ I couldn't process your request right now.\n\n"
            "Please try again in a moment."
        )


# ============================================================
# ADMIN PANEL
# ============================================================

@router.message(
    StateFilter("*"),
    Command("admin"),
)
async def admin_panel_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ You don't have permission to access "
            "the admin panel."
        )
        return

    await message.answer(
        "🔐 <b>SAK AI Admin Panel</b>\n\n"
        "Choose an option:",
        parse_mode="HTML",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# ADMIN — ADD UPDATE
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "➕ Add Update",
)
async def admin_add_update_handler(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    await state.clear()

    await state.set_state(
        AdminStates.waiting_for_update_title
    )

    await message.answer(
        "➕ <b>Add Update</b>\n\n"
        "Please enter the update title:",
        parse_mode="HTML",
    )


@router.message(
    AdminStates.waiting_for_update_title,
    F.text,
)
async def admin_update_title_handler(
    message: Message,
    state: FSMContext,
):
    title = message.text.strip()

    if not title:
        await message.answer(
            "⚠️ Please enter a valid update title."
        )
        return

    if len(title) > 255:
        await message.answer(
            "⚠️ Title is too long. "
            "Please keep it under 255 characters."
        )
        return

    await state.update_data(
        update_title=title
    )

    await state.set_state(
        AdminStates.waiting_for_update_content
    )

    await message.answer(
        "📝 Now enter the update content:"
    )


@router.message(
    AdminStates.waiting_for_update_content,
    F.text,
)
async def admin_update_content_handler(
    message: Message,
    state: FSMContext,
):
    content = message.text.strip()

    if not content:
        await message.answer(
            "⚠️ Please enter valid update content."
        )
        return

    if len(content) > 4000:
        await message.answer(
            "⚠️ Update content is too long. "
            "Please keep it under 4,000 characters."
        )
        return

    data = await state.get_data()

    async with AsyncSessionLocal() as session:
        update = Update(
            title=data["update_title"],
            content=content,
            is_published=True,
        )

        session.add(update)
        await session.commit()
        await session.refresh(update)

    await state.clear()

    await message.answer(
        "✅ <b>Update published successfully!</b>\n\n"
        f"<b>#{update.id} — {update.title}</b>\n"
        f"{update.content}",
        parse_mode="HTML",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# ADMIN — MANAGE UPDATES
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "📋 Manage Updates",
)
async def admin_manage_updates_handler(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    await state.clear()

    async with AsyncSessionLocal() as session:
        updates = await get_published_updates(session)

    if not updates:
        await message.answer(
            "📋 <b>Manage Updates</b>\n\n"
            "There are currently no published updates.",
            parse_mode="HTML",
            reply_markup=admin_keyboard(),
        )
        return

    text = "📋 <b>Published Updates</b>\n\n"

    for update in updates:
        text += (
            f"<b>#{update.id} — {update.title}</b>\n"
            f"{update.content}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=manage_updates_keyboard(updates),
    )


# ============================================================
# ADMIN — DELETE UPDATE
# ============================================================

@router.message(
    StateFilter("*"),
    F.text.regexp(r"^🗑️ Delete #\d+$"),
)
async def admin_delete_update_handler(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    try:
        update_id = int(
            message.text.split("#")[1]
        )
    except (ValueError, IndexError):
        await message.answer(
            "⚠️ Invalid update ID."
        )
        return

    async with AsyncSessionLocal() as session:
        update = await session.get(
            Update,
            update_id,
        )

        if update is None:
            await message.answer(
                "⚠️ Update not found.",
                reply_markup=admin_keyboard(),
            )
            return

        await session.delete(update)
        await session.commit()

    await state.clear()

    await message.answer(
        f"✅ Update #{update_id} deleted successfully.",
        reply_markup=admin_keyboard(),
    )


# ============================================================
# ADMIN — NAVIGATION
# ============================================================

@router.message(
    StateFilter("*"),
    F.text == "🔙 Admin Panel",
)
async def admin_panel_navigation_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔐 <b>SAK AI Admin Panel</b>\n\n"
        "Choose an option:",
        parse_mode="HTML",
        reply_markup=admin_keyboard(),
    )


@router.message(
    StateFilter("*"),
    F.text == "🔙 Main Menu",
)
async def admin_main_menu_navigation_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "🏠 <b>Main Menu</b>\n\n"
        "What would you like to do?",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ============================================================
# UNKNOWN TEXT
# ============================================================

@router.message(F.text)
async def unknown_text_handler(
    message: Message,
    state: FSMContext,
):
    current_state = await state.get_state()

    if current_state is not None:
        return

    await message.answer(
        "I didn't quite understand that. 🤔\n\n"
        "Please choose an option from the menu.",
        reply_markup=main_menu_keyboard(),
    )