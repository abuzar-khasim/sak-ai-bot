from sqlalchemy import select

from app.database.models import User , Lead , Update, Conversation, Message


async def get_user(session, telegram_id: int):
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )

    return result.scalar_one_or_none()


async def create_user(
    session,
    telegram_id: int,
    username: str | None,
    name: str,
    age: int,
    category: str,
):
    user = User(
        telegram_id=telegram_id,
        username=username,
        name=name,
        age=age,
        category=category,
    )

    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


async def create_lead(
    session,
    telegram_id: int,
    name: str,
    email: str,
    service: str,
    requirement: str,
):
    lead = Lead(
        telegram_id=telegram_id,
        name=name,
        email=email,
        service=service,
        requirement=requirement,
    )

    session.add(lead)

    await session.commit()
    await session.refresh(lead)

    return lead    

async def get_published_updates(session, limit: int = 5):
    result = await session.execute(
        select(Update)
        .where(Update.is_published.is_(True))
        .order_by(Update.created_at.desc())
        .limit(limit)
    )

    return result.scalars().all()

async def get_all_updates(session, limit: int = 20):
    result = await session.execute(
        select(Update)
        .order_by(Update.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def delete_update(session, update_id: int):
    result = await session.execute(
        select(Update).where(Update.id == update_id)
    )
    update = result.scalar_one_or_none()

    if update is None:
        return False

    await session.delete(update)
    await session.commit()

    return True


async def get_or_create_conversation(
    session,
    telegram_id: int,
):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.telegram_id == telegram_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )

    conversation = result.scalar_one_or_none()

    if conversation is not None:
        return conversation

    conversation = Conversation(
        telegram_id=telegram_id,
        title="New Conversation",
    )

    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    return conversation


async def create_message(
    session,
    conversation_id: int,
    role: str,
    content: str,
    model: str | None = None,
):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model,
    )

    session.add(message)
    await session.commit()
    await session.refresh(message)

    return message


async def get_recent_messages(
    session,
    conversation_id: int,
    limit: int = 20,
):
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    messages = result.scalars().all()

    return list(reversed(messages))