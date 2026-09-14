from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request

from app.ai.http_client import create_http_client
from app.ai.router import LLMRouter
from app.bot.handlers import router
from app.config.settings import settings
from app.database.database import init_db


# ============================================================
# TELEGRAM BOT
# ============================================================

bot = Bot(
    token=settings.telegram_bot_token
)

dp = Dispatcher()

dp.include_router(router)


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Starting SAK AI...")

    # --------------------------------------------------------
    # DATABASE INITIALIZATION
    # --------------------------------------------------------

    try:
        await init_db()

        print(
            "✅ Database initialized successfully!"
        )

    except Exception as error:

        print(
            "❌ Database initialization failed: "
            f"{type(error).__name__}: {error}"
        )

    # --------------------------------------------------------
    # AI HTTP CLIENT + LLM ROUTER
    # --------------------------------------------------------

    http_client = create_http_client()

    llm_router = LLMRouter(
        http_client
    )

    # IMPORTANT:
    # Make the LLM router available to handlers.py.
    #
    # ai_chat_handler() does NOT receive llm_router
    # as an aiogram dependency.
    #
    # Instead it accesses:
    #
    # router.llm_router
    #
    router.llm_router = llm_router

    # Also expose them through FastAPI application state.
    app.state.http_client = http_client
    app.state.llm_router = llm_router

    print(
        "✅ AI HTTP client initialized"
    )

    print(
        "✅ LLM router initialized"
    )

    # --------------------------------------------------------
    # TELEGRAM WEBHOOK
    # --------------------------------------------------------

    try:

        base_url = (
            settings.webhook_base_url
            .strip()
            .rstrip("/")
        )

        if not base_url:

            print(
                "❌ WEBHOOK_BASE_URL is empty "
                "or not configured."
            )

        else:

            webhook_url = (
                f"{base_url}/telegram/webhook"
            )

            print(
                "🔧 Setting Telegram webhook..."
            )

            print(
                f"🔗 Webhook URL: {webhook_url}"
            )

            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
            )

            # ------------------------------------------------
            # VERIFY WEBHOOK
            # ------------------------------------------------

            webhook_info = (
                await bot.get_webhook_info()
            )

            print(
                "✅ Telegram webhook configured "
                "successfully!"
            )

            print(
                f"🔗 Registered URL: "
                f"{webhook_info.url}"
            )

            print(
                f"📨 Pending updates: "
                f"{webhook_info.pending_update_count}"
            )

            if webhook_info.last_error_message:

                print(
                    "⚠️ Telegram webhook last error: "
                    f"{webhook_info.last_error_message}"
                )

    except Exception as error:

        print(
            "❌ Failed to configure Telegram "
            "webhook: "
            f"{type(error).__name__}: {error}"
        )

    # --------------------------------------------------------
    # STARTUP COMPLETE
    # --------------------------------------------------------

    print(
        "✅ SAK AI startup complete!"
    )

    # --------------------------------------------------------
    # APPLICATION RUNNING
    # --------------------------------------------------------

    yield

    # ========================================================
    # SHUTDOWN
    # ========================================================

    print(
        "🛑 Shutting down SAK AI..."
    )

    # --------------------------------------------------------
    # CLOSE AI HTTP CLIENT
    # --------------------------------------------------------

    try:

        await http_client.aclose()

        print(
            "✅ AI HTTP client closed"
        )

    except Exception as error:

        print(
            "⚠️ Failed to close AI HTTP client: "
            f"{type(error).__name__}: {error}"
        )

    # --------------------------------------------------------
    # CLOSE TELEGRAM BOT SESSION
    # --------------------------------------------------------

    try:

        # IMPORTANT:
        #
        # Do NOT delete the Telegram webhook here.
        #
        # Render can restart/redeploy the service.
        # Deleting the webhook during shutdown can cause
        # Telegram updates to stop being delivered.
        #
        # We only close the bot HTTP session.

        await bot.session.close()

        print(
            "✅ Telegram bot session closed"
        )

    except Exception as error:

        print(
            "⚠️ Failed to close Telegram bot "
            "session: "
            f"{type(error).__name__}: {error}"
        )

    print(
        "✅ SAK AI shutdown complete."
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SAK AI API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "service": "SAK AI",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "SAK AI",
    }


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
):

    try:

        # ----------------------------------------------------
        # Read Telegram update JSON
        # ----------------------------------------------------

        update_data = await request.json()

        # ----------------------------------------------------
        # Convert JSON into aiogram Update
        # ----------------------------------------------------

        update = Update.model_validate(
            update_data
        )

        # ----------------------------------------------------
        # Send update to aiogram dispatcher
        # ----------------------------------------------------

        await dp.feed_update(
            bot,
            update,
        )

        return {
            "ok": True,
        }

    except Exception as error:

        print(
            "❌ Telegram webhook processing error: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "ok": False,
            "error": str(error),
        }