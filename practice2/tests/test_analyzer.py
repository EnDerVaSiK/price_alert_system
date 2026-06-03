import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../analyzer')))
import main as analyzer_main

class FakeTicker:
    def __init__(self, id, symbol):
        self.id = id
        self.symbol = symbol

class FakeSub:
    def __init__(self, price):
        self.last_notified_price = price

def setup_redis_mock(mock_redis, prices_dict):
    async def mock_brpop(*args, **kwargs):
        analyzer_main.shutdown_event.set()
        return ("queue:analyze", json.dumps({"prices": prices_dict}))
    mock_redis.brpop.side_effect = mock_brpop

@pytest.mark.asyncio
@patch.object(analyzer_main.Redis, 'from_url')
@patch.object(analyzer_main, 'AsyncSessionLocal')
async def test_analyzer_first_price(mock_db_maker, mock_redis_from_url):
    analyzer_main.shutdown_event.clear()
    
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    setup_redis_mock(mock_redis, {"SBER": 300.0})
    
    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_db_maker.return_value = mock_cm
    
    mock_session.scalar.return_value = FakeTicker(1, "SBER")
    
    fake_sub = FakeSub(None) 
    mock_session.execute.return_value = [(fake_sub, 123456)]

    await analyzer_main.run()

    mock_redis.lpush.assert_called_once()
    payload = json.loads(mock_redis.lpush.call_args[0][1])
    assert payload["telegram_id"] == 123456
    assert "Вы начали отслеживать" in payload["text"]
    assert fake_sub.last_notified_price == 300.0

@pytest.mark.asyncio
@patch.object(analyzer_main.Redis, 'from_url')
@patch.object(analyzer_main, 'AsyncSessionLocal')
async def test_analyzer_price_changed(mock_db_maker, mock_redis_from_url):
    analyzer_main.shutdown_event.clear()
    
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    setup_redis_mock(mock_redis, {"SBER": 310.0})
    
    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_db_maker.return_value = mock_cm
    
    mock_session.scalar.return_value = FakeTicker(1, "SBER")
    
    fake_sub = FakeSub(300.0)
    mock_session.execute.return_value = [(fake_sub, 123456)]

    await analyzer_main.run()

    mock_redis.lpush.assert_called_once()
    payload = json.loads(mock_redis.lpush.call_args[0][1])
    assert payload["telegram_id"] == 123456
    assert "Выросла" in payload["text"]
    assert fake_sub.last_notified_price == 310.0

@pytest.mark.asyncio
@patch.object(analyzer_main.Redis, 'from_url')
@patch.object(analyzer_main, 'AsyncSessionLocal')
async def test_analyzer_price_unchanged(mock_db_maker, mock_redis_from_url):
    analyzer_main.shutdown_event.clear()
    
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    setup_redis_mock(mock_redis, {"SBER": 300.0})
    
    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_db_maker.return_value = mock_cm
    
    mock_session.scalar.return_value = FakeTicker(1, "SBER")
    
    fake_sub = FakeSub(300.0)
    mock_session.execute.return_value = [(fake_sub, 123456)]

    await analyzer_main.run()

    mock_redis.lpush.assert_not_called()
