import sys
import os
import json
import httpx
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

if "main" in sys.modules:
    del sys.modules["main"]
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../parser')))

from main import run as parser_run, shutdown_event

@pytest.fixture
def moex_mock_response():
    return {
        "marketdata": {
            "columns": ["SECID", "LAST"],
            "data": [["SBER", 300.5], ["GAZP", 150.0]]
        }
    }

@pytest.mark.asyncio
@patch("main.Redis.from_url")
@patch("httpx.AsyncClient.get")
async def test_parser_successful_moex_response(mock_get, mock_redis_from_url, moex_mock_response):
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    async def mock_brpop(*args, **kwargs):
        if not shutdown_event.is_set():
            shutdown_event.set()
            return ("queue:parse", json.dumps({"tickers": ["SBER", "GAZP"]}))
        return None
    mock_redis.brpop.side_effect = mock_brpop

    # ИСПОЛЬЗУЕМ MagicMock вместо AsyncMock
    mock_resp = MagicMock()
    mock_resp.json.return_value = moex_mock_response 
    mock_get.return_value = mock_resp

    await parser_run()

    mock_redis.lpush.assert_called_once()
    queue, payload = mock_redis.lpush.call_args[0]
    assert queue == "queue:analyze"
    data = json.loads(payload)
    assert data["prices"]["SBER"] == 300.5

@pytest.mark.asyncio
@patch("main.Redis.from_url")
@patch("httpx.AsyncClient.get")
async def test_parser_broken_json(mock_get, mock_redis_from_url):
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    async def mock_brpop(*args, **kwargs):
        if not shutdown_event.is_set():
            shutdown_event.set()
            return ("queue:parse", json.dumps({"tickers": ["SBER"]}))
        return None
    mock_redis.brpop.side_effect = mock_brpop

    # ИСПОЛЬЗУЕМ MagicMock
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"marketdata": {}}
    mock_get.return_value = mock_resp

    await parser_run()
    mock_redis.lpush.assert_not_called()

@pytest.mark.asyncio
@patch("main.Redis.from_url")
@patch("httpx.AsyncClient.get")
async def test_parser_http_error(mock_get, mock_redis_from_url):
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis
    
    async def mock_brpop(*args, **kwargs):
        if not shutdown_event.is_set():
            shutdown_event.set()
            return ("queue:parse", json.dumps({"tickers": ["SBER"]}))
        return None
    mock_redis.brpop.side_effect = mock_brpop

    mock_get.side_effect = httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())

    await parser_run()
    mock_redis.lpush.assert_not_called()