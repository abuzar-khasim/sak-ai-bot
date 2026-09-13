import asyncio

from app.database.database import AsyncSessionLocal, init_db
from app.database.models import Update


async def add_update():
    await init_db()

    async with AsyncSessionLocal() as session:
        update = Update(
            title="SAK AI is Live! 🚀",
            content=(
                "Welcome to SAK AI!\n\n"
                "We are building AI-powered solutions, "
                "intelligent automations, and AI agents."
            ),
            is_published=True,
        )

        session.add(update)
        await session.commit()

        print("✅ Test update added successfully!")


asyncio.run(add_update())