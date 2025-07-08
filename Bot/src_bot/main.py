import logging
import os
import asyncpg
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

connection_pool = None

async def init_db_pool():
    global connection_pool
    try:
        connection_pool = await asyncpg.create_pool(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def ensure_user_exists(telegram_id, first_name, last_name, username):
    if not connection_pool:
        logger.error("Database pool not initialized")
        return None

    try:
        async with connection_pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (telegram_id, first_name, last_name, username)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_id) DO UPDATE
                SET first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    username = EXCLUDED.username
                RETURNING id
                """,
                telegram_id, first_name, last_name, username
            )
            return user_id
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return None


async def save_request(user_id, prompt, response):
    if not connection_pool:
        logger.error("Database pool not initialized")
        return

    try:
        async with connection_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO requests (user_id, prompt, response) VALUES ($1, $2, $3)",
                user_id, prompt, response
            )
    except Exception as e:
        logger.error(f"Error saving request: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await ensure_user_exists(
        user.id,
        user.first_name,
        user.last_name,
        user.username
    )

    if user_id:
        await update.message.reply_text(
            f"Привет, {user.first_name}! Я запомнил тебя. Пиши мне что угодно, и я сгенерирую ответ.")
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! К сожалению, не смог сохранить тебя в базе. Но ты все равно можешь пользоваться ботом.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто отправь мне любое текстовое сообщение, и я обработаю его с помощью нейросети!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message.text

    user_id = await ensure_user_exists(
        user.id,
        user.first_name,
        user.last_name,
        user.username
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json={"prompt": user_message},
                timeout=180.0
            )

        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("generated_text", "Пустой ответ от API")
            await update.message.reply_text(generated_text)

            if user_id:
                await save_request(user_id, user_message, generated_text)
        else:
            error_msg = f"Ошибка API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            await update.message.reply_text("⚠️ Произошла ошибка при обработке запроса. Попробуйте позже.")

            if user_id:
                await save_request(user_id, user_message, f"ERROR: {response.status_code}")

    except Exception as e:
        logger.exception("Ошибка при обработке сообщения")
        await update.message.reply_text(f"❌ Критическая ошибка: {str(e)}")

        if user_id:
            await save_request(user_id, user_message, f"EXCEPTION: {str(e)}")

async def on_startup(application: Application):
    await init_db_pool()
    logger.info("Bot started successfully")

async def on_shutdown(application: Application):
    global connection_pool
    if connection_pool:
        await connection_pool.close()
        logger.info("Database connection pool closed")


def main():
    application = (Application.builder()
                   .token(TELEGRAM_TOKEN)
                   .post_init(on_startup)
                   .post_shutdown(on_shutdown)
                   .build())

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()
    logger.info("Бот запущен")
    logger.info(
        f"Pool stats: connections={connection_pool.get_size()}, "
        f"free={connection_pool.get_free_size()}, "
        f"queue={connection_pool.get_queue_size()}"
    )

if __name__ == "__main__":
    main()