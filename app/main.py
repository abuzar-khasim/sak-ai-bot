from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request

from app.ai.http_client import create_http_client
from app.ai.router import LLMRouter
from app.bot.handlers import router
from app.config.settings import settings
from app.database.database import init_db


# ---------------------------------------------------------
# Telegram Bot
# ---------------------------------------------------------

bot = Bot(token=settings.telegram_bot_token)

dp = Dispatcher()
dp.include_router(router)


# ---------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting SAK AI...")

    # -----------------------------------------------------
    # Initialize Database
    # -----------------------------------------------------
    try:
        await init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # -----------------------------------------------------
    # Initialize AI HTTP Client + LLM Router
    # -----------------------------------------------------
    http_client = create_http_client()
    llm_router = LLMRouter(http_client)

    app.state.http_client = http_client
    app.state.llm_router = llm_router

    print("✅ AI HTTP client initialized")
    print("✅ LLM router initialized")

    # -----------------------------------------------------
    # Configure Telegram Webhook
    # -----------------------------------------------------
    try:
        base_url = settings.webhook_base_url.strip().rstrip("/")

        if not base_url:
            print("❌ WEBHOOK_BASE_URL is empty or not configured.")
        else:
            webhook_url = f"{base_url}/telegram/webhook"

            print("🔧 Setting Telegram webhook...")
            print(f"🔗 Webhook URL: {webhook_url}")

            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
            )

            # Verify webhook with Telegram
            webhook_info = await bot.get_webhook_info()

            print("✅ Telegram webhook configured successfully!")
            print(f"🔗 Registered URL: {webhook_info.url}")
            print(
                f"📨 Pending updates: "
                f"{webhook_info.pending_update_count}"
            )

            if webhook_info.last_error_message:
                print(
                    f"⚠️ Telegram webhook last error: "
                    f"{webhook_info.last_error_message}"
                )

    except Exception as e:
        print(f"❌ Failed to configure Telegram webhook: {e}")

    print("✅ SAK AI startup complete!")

    # -----------------------------------------------------
    # Application Running
    # -----------------------------------------------------
    yield

    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------
    print("🛑 Shutting down SAK AI...")

    # Close shared AI HTTP client
    await http_client.aclose()
    print("✅ AI HTTP client closed")

    # IMPORTANT:
    # Do NOT delete the Telegram webhook here.
    #
    # Render may restart/redeploy the service and deleting
    # the webhook during shutdown can cause Telegram updates
    # to stop being delivered.
    #
    # We only close the bot HTTP session.
    await bot.session.close()

    print("✅ SAK AI shutdown complete.")


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="SAK AI API",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "SAK AI",
        "status": "running",
    }


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SAK AI",
    }


# ---------------------------------------------------------
# Telegram Webhook
# ---------------------------------------------------------

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    try:
        update_data = await request.json()

        # Convert incoming Telegram JSON into an aiogram Update
        update = Update.model_validate(update_data)

        # Send update to aiogram dispatcher
        await dp.feed_update(
            bot,
            update,
        )

        return {
            "ok": True,
        }

    except Exception as e:
        print(f"❌ Telegram webhook processing error: {e}")

        return {
            "ok": False,
            "error": str(e),
        }