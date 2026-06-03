import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_redis():
    """Базовая фикстура для Redis с заглушкой brpop, чтобы циклы не зависали"""
    mock = AsyncMock()
    mock.brpop.return_value = None
    return mock

@pytest.fixture
def mock_db_session():
    """Базовая фикстура для сессии БД"""
    session = AsyncMock()
    # Настраиваем базовые ответы для execute и scalar
    session.execute.return_value = AsyncMock()
    session.scalar.return_value = None
    return session
