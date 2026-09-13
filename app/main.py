from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from fastapi import FastAPI, Request

from app.bot.handlers import router
from app.config.settings import settings
from app.database.database import init_db


bot = Bot(token=settings.telegram_bot_token)

dp = Dispatcher()
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db()

    # Set Telegram webhook only when deployed
    if settings.webhook_base_url:
        webhook_url = (
            f"{settings.webhook_base_url}/telegram/webhook"
        )

        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
        )

        print(f"✅ Telegram webhook set: {webhook_url}")

    yield

    # Cleanup
    if settings.webhook_base_url:
        await bot.delete_webhook()

    await bot.session.close()


app = FastAPI(
    title="SAK AI API",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "service": "SAK AI",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SAK AI",
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update_data = await request.json()

    await dp.feed_raw_update(
        bot,
        update_data,
    )

    return {"ok": True}