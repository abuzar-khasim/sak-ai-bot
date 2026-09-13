from sqlalchemy import select

from app.database.models import User


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