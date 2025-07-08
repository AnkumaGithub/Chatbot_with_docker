import pytest
from unittest.mock import AsyncMock, MagicMock
from src_bot.main import start, handle_message


@pytest.mark.asyncio
async def test_start_command():
    update = MagicMock()
    context = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123
    update.effective_user.first_name = "Test"

    await start(update, context)
    assert "Привет, Test!" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_message_handling(mocker):
    update = MagicMock()
    context = MagicMock()
    update.message.text = "Hello"

    # Мокируем API и DB
    mocker.patch("main.ensure_user_exists", return_value=1)
    mocker.patch("main.httpx.AsyncClient.post",
                 return_value=MagicMock(status_code=200, json=lambda: {"generated_text": "Hi"}))

    await handle_message(update, context)
    assert "Hi" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_db_error(mocker):
    update = MagicMock()
    context = MagicMock()
    update.message.text = "Hello"

    mocker.patch("main.ensure_user_exists", return_value=None)

    await handle_message(update, context)
    assert "Ошибка" in update.message.reply_text.call_args[0][0]