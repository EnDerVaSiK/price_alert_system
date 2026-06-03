import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path = [p for p in sys.path if not any(x in p for x in ['api-gateway', 'scheduler', 'parser', 'analyzer', 'notifier'])]
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scheduler')))
if "main" in sys.modules:
    del sys.modules["main"]

from main import run as scheduler_run, shutdown_event

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('main.AsyncSessionLocal')
async def test_scheduler_successful_push(mock_db_maker, mock_redis_from_url):
    shutdown_event.clear() # Очищаем ивент перед тестом
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    mock_session = AsyncMock()
    mock_db_maker.return_value.__aenter__.return_value = mock_session
    
    # Чтобы воркер вошел в цикл 1 раз, мы устанавливаем shutdown_event во время обращения к БД
    async def mock_execute(*args, **kwargs):
        shutdown_event.set()
        mock_result = MagicMock()
        mock_result.all.return_value = [("SBER",), ("GAZP",)]
        return mock_result
        
    mock_session.execute.side_effect = mock_execute
    
    await scheduler_run()
    
    mock_redis.lpush.assert_called_once()
    queue, payload = mock_redis.lpush.call_args[0]
    assert queue == "queue:parse"
    assert json.loads(payload)["tickers"] == ["SBER", "GAZP"]

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('main.AsyncSessionLocal')
async def test_scheduler_empty_db(mock_db_maker, mock_redis_from_url):
    shutdown_event.clear()
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    mock_session = AsyncMock()
    mock_db_maker.return_value.__aenter__.return_value = mock_session
    
    async def mock_execute(*args, **kwargs):
        shutdown_event.set()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        return mock_result
        
    mock_session.execute.side_effect = mock_execute
    
    await scheduler_run()
    mock_redis.lpush.assert_not_called()

@pytest.mark.asyncio
@patch('redis.asyncio.Redis.from_url')
@patch('main.AsyncSessionLocal')
async def test_scheduler_db_error(mock_db_maker, mock_redis_from_url):
    shutdown_event.clear()
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    mock_session = AsyncMock()
    mock_db_maker.return_value.__aenter__.return_value = mock_session
    
    async def mock_execute(*args, **kwargs):
        shutdown_event.set()
        raise Exception("DB Down")
        
    mock_session.execute.side_effect = mock_execute
    
    await scheduler_run()
    mock_redis.lpush.assert_not_called()