from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request

from app.ai.http_client import create_http_client
from app.ai.router import LLMRouter
from app.bot.handlers import router
from app.config.settings import settings
from app.database.database import init_db


# ============================================================
# TELEGRAM BOT
# ============================================================

bot = Bot(
    token=settings.telegram_bot_token,
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

        print("✅ Database initialized successfully!")

    except Exception as error:
        print(
            "❌ Database initialization failed: "
            f"{type(error).__name__}: {error}"
        )
        raise

    # --------------------------------------------------------
    # AI HTTP CLIENT + LLM ROUTER
    # --------------------------------------------------------

    http_client = create_http_client()

    llm_router = LLMRouter(
        http_client,
    )

    # Make LLM router available to handlers.py
    router.llm_router = llm_router

    # Expose through FastAPI application state
    app.state.http_client = http_client
    app.state.llm_router = llm_router

    print("✅ AI HTTP client initialized")
    print("✅ LLM router initialized")

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

            print("🔧 Setting Telegram webhook...")
            print(f"🔗 Webhook URL: {webhook_url}")

            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.telegram_webhook_secret,
                drop_pending_updates=True,
            )

            webhook_info = await bot.get_webhook_info()

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

    print("✅ SAK AI startup complete!")

    yield

    # ========================================================
    # SHUTDOWN
    # ========================================================

    print("🛑 Shutting down SAK AI...")

    # --------------------------------------------------------
    # CLOSE AI HTTP CLIENT
    # --------------------------------------------------------

    try:
        await http_client.aclose()

        print("✅ AI HTTP client closed")

    except Exception as error:
        print(
            "⚠️ Failed to close AI HTTP client: "
            f"{type(error).__name__}: {error}"
        )

    # --------------------------------------------------------
    # CLOSE TELEGRAM BOT SESSION
    # --------------------------------------------------------

    try:
        # Do NOT delete the Telegram webhook here.
        await bot.session.close()

        print("✅ Telegram bot session closed")

    except Exception as error:
        print(
            "⚠️ Failed to close Telegram bot "
            "session: "
            f"{type(error).__name__}: {error}"
        )

    print("✅ SAK AI shutdown complete.")


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
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
    ),
):
    # --------------------------------------------------------
    # VERIFY TELEGRAM WEBHOOK SECRET
    # --------------------------------------------------------

    if (
        x_telegram_bot_api_secret_token
        != settings.telegram_webhook_secret
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook authentication",
        )

    try:
        # ----------------------------------------------------
        # READ TELEGRAM UPDATE
        # ----------------------------------------------------

        update_data = await request.json()

        # ----------------------------------------------------
        # CONVERT JSON TO AIOGRAM UPDATE
        # ----------------------------------------------------

        update = Update.model_validate(
            update_data,
        )

        # ----------------------------------------------------
        # PROCESS UPDATE
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

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        ) from error