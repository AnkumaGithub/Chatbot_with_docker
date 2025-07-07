import asyncio
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


async def get_db_connection():
    return await asyncpg.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто отправь мне любое текстовое сообщение, и я обработаю его с помощью нейросети!")

async def ensure_user_exists(telegram_id, first_name, last_name, username):
    try:
        conn = await get_db_connection()
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
        await conn.close()
        return user_id
    except Exception as e:
        logger.error(f"DB error: {e}")
        return None


async def save_request(user_id, prompt, response):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO requests (user_id, prompt, response) VALUES (%s, %s, %s)",
                (user_id, prompt, response)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving request: {e}")
    finally:
        conn.close()


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



def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()
    logger.info("Бот запущен")


if __name__ == "__main__":
    main()