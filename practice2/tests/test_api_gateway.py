import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api-gateway')))

# Принудительно очищаем кэш импортов Python, чтобы он не подсунул main.py от другого сервиса
if "main" in sys.modules:
    del sys.modules["main"]

import main as api_main

class FakeUser:
    def __init__(self):
        self.id = 1
        self.telegram_id = 123456789

class FakeTicker:
    def __init__(self):
        self.id = 1
        self.symbol = "SBER"

@pytest.fixture
def mock_user_message():
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 123456789
    msg.answer = AsyncMock() 
    return msg

@pytest.fixture
def mock_callback_query():
    cb = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = 123456789
    cb.data = "sub_SBER"
    
    cb.message = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    return cb

@pytest.mark.asyncio
@patch.object(api_main, 'AsyncSessionLocal')
async def test_cmd_start_new_user(mock_session_maker, mock_user_message):
    mock_session = AsyncMock()
    mock_session.scalar.return_value = None
    mock_session.add = MagicMock() 
    
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_session_maker.return_value = mock_cm

    await api_main.cmd_start(mock_user_message)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_user_message.answer.assert_called_once()

@pytest.mark.asyncio
@patch.object(api_main, 'AsyncSessionLocal')
async def test_process_subscription_success(mock_session_maker, mock_callback_query):
    mock_session = AsyncMock()
    mock_session.scalar.side_effect = [FakeUser(), FakeTicker(), None]
    mock_session.add = MagicMock() 
    
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_session_maker.return_value = mock_cm

    await api_main.process_subscription(mock_callback_query)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()
    mock_callback_query.message.answer.assert_called_once()
    assert "успешно подписались" in mock_callback_query.message.answer.call_args[0][0]

@pytest.mark.asyncio
@patch.object(api_main, 'AsyncSessionLocal')
async def test_cmd_start_db_error(mock_session_maker, mock_user_message):
    mock_session = AsyncMock()
    mock_session.scalar.side_effect = Exception("DB Connection Lost")
    
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_session_maker.return_value = mock_cm

    with pytest.raises(Exception, match="DB Connection Lost"):
        await api_main.cmd_start(mock_user_message)
