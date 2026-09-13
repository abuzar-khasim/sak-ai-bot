import asyncio

from sqlalchemy import text

from app.database.database import engine, init_db


async def test_database():
    try:
        # Create tables
        await init_db()

        # Test connection
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print("Database result:", result.scalar())

        print("✅ PostgreSQL connection successful!")

    except Exception as e:
        print("❌ Database connection failed:")
        print(e)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_database())