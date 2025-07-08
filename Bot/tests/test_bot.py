import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src_bot.main import start, handle_message


@pytest.mark.asyncio
async def test_start_command():
    update = AsyncMock()
    context = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123
    update.effective_user.first_name = "Test"

    with patch('src_bot.main.ensure_user_exists', new_callable=AsyncMock) as mock_ensure:
        mock_ensure.return_value = 1

        await start(update, context)

        update.message.reply_text.assert_awaited_once()
        assert "Привет, Test!" in update.message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_message_handling():
    update = AsyncMock()
    context = MagicMock()
    update.message.text = "Hello"

    with (
        patch('src_bot.main.ensure_user_exists', new_callable=AsyncMock) as mock_ensure,
        patch('src_bot.main.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post
    ):
        mock_ensure.return_value = 1
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"generated_text": "Hi"}
        mock_post.return_value = mock_response

        await handle_message(update, context)

        update.message.reply_text.assert_awaited_once_with("Hi")


@pytest.mark.asyncio
async def test_db_error():
    update = AsyncMock()
    context = MagicMock()
    update.message.text = "Hello"

    with patch('src_bot.main.ensure_user_exists', new_callable=AsyncMock) as mock_ensure:
        mock_ensure.return_value = None

        await handle_message(update, context)

        update.message.reply_text.assert_awaited_once()
        assert "базы данных" in update.message.reply_text.call_args[0][0]