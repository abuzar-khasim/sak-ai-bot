from sqlalchemy import select

from app.database.models import User , Lead ,   Update


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
