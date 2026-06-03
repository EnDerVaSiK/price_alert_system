import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path = [p for p in sys.path if not any(x in p for x in ['api-gateway', 'scheduler', 'parser', 'analyzer', 'notifier'])]
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../notifier')))
if "main" in sys.modules:
    del sys.modules["main"]

os.environ["TELEGRAM_BOT_TOKEN"] = "fake_token_for_tests"

from main import run as notifier_run, shutdown_event

def setup_redis_mock(mock_redis, payload_dict):
    async def mock_brpop(*args, **kwargs):
        shutdown_event.set()
        return ("queue:notify", json.dumps(payload_dict))
    mock_redis.brpop.side_effect = mock_brpop

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('httpx.AsyncClient')
async def test_notifier_successful_send(mock_http_client_class, mock_redis_from_url):
    shutdown_event.clear()
    
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    payload = {"telegram_id": 123456, "text": "Тестовое сообщение"}
    setup_redis_mock(mock_redis, payload)
    
    mock_client = AsyncMock()
    mock_http_client_class.return_value.__aenter__.return_value = mock_client
    
    # ИСПОЛЬЗУЕМ СИНХРОННЫЙ MagicMock для ответа, чтобы raise_for_status не ругался
    mock_resp = MagicMock() 
    mock_client.post.return_value = mock_resp

    await notifier_run()

    mock_client.post.assert_called_once()
    kwargs = mock_client.post.call_args[1]
    assert kwargs["json"]["chat_id"] == 123456
    assert kwargs["json"]["text"] == "Тестовое сообщение"

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('httpx.AsyncClient')
async def test_notifier_formatting_first_price(mock_http_client_class, mock_redis_from_url):
    shutdown_event.clear()
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    text = "📈 Вы начали отслеживать <b>SBER</b>.\nТекущая цена: <b>300.0 ₽</b>"
    setup_redis_mock(mock_redis, {"telegram_id": 123, "text": text})

    mock_client = AsyncMock()
    mock_http_client_class.return_value.__aenter__.return_value = mock_client
    mock_resp = MagicMock()
    mock_client.post.return_value = mock_resp

    await notifier_run()

    mock_client.post.assert_called_once()
    sent_text = mock_client.post.call_args[1]["json"]["text"]
    assert "Вы начали отслеживать" in sent_text

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('httpx.AsyncClient')
async def test_notifier_formatting_changed_price(mock_http_client_class, mock_redis_from_url):
    shutdown_event.clear()
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    text = "🟢 Выросла!\n\nАкция: <b>SBER</b>\nСтарая цена: <s>300.0 ₽</s>\nНовая цена: <b>310.0 ₽</b>"
    setup_redis_mock(mock_redis, {"telegram_id": 123, "text": text})

    mock_client = AsyncMock()
    mock_http_client_class.return_value.__aenter__.return_value = mock_client
    mock_resp = MagicMock()
    mock_client.post.return_value = mock_resp

    await notifier_run()

    mock_client.post.assert_called_once()
    sent_text = mock_client.post.call_args[1]["json"]["text"]
    assert "🟢 Выросла" in sent_text
    assert "<s>300.0 ₽</s>" in sent_text