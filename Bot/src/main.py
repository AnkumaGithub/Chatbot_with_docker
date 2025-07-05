import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот с интеграцией LLM. Просто напиши мне что-нибудь, и я сгенерирую ответ.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто отправь мне любое текстовое сообщение, и я обработаю его с помощью нейросети!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

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
        else:
            error_msg = f"Ошибка API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            await update.message.reply_text("⚠️ Произошла ошибка при обработке запроса. Попробуйте позже.")

    except httpx.ConnectError:
        logger.error("Не удалось подключиться к API")
        await update.message.reply_text("🔌 API недоступно! Проверьте запущен ли сервер.")
    except Exception as e:
        logger.exception("Ошибка при обработке сообщения")
        await update.message.reply_text(f"❌ Критическая ошибка: {str(e)}")


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()
    logger.info("Бот запущен")


if __name__ == "__main__":
    main()