import asyncio
import json
import logging
import os
import signal
import sys
from redis.asyncio import Redis
from sqlalchemy.future import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import AsyncSessionLocal, Ticker, Subscription, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scheduler")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
shutdown_event = asyncio.Event()

def handle_shutdown(sig: int) -> None:
    logger.info("Graceful Shutdown Scheduler...")
    shutdown_event.set()

async def run():
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Scheduler запущен. Интервал: 60 сек.")
    
    while not shutdown_event.is_set():
        try:
            async with AsyncSessionLocal() as session:
                # Достаем только те тикеры, на которые есть хотя бы одна подписка
                stmt = select(Ticker.symbol).join(Subscription).distinct()
                result = await session.execute(stmt)
                active_tickers = [row[0] for row in result.all()]
                
                if active_tickers:
                    logger.info(f"Найдено {len(active_tickers)} активных тикеров. Отправка в парсер.")
                    payload = {"tickers": active_tickers}
                    await redis_client.lpush("queue:parse", json.dumps(payload))
                else:
                    logger.info("Нет активных подписок. Пропуск цикла.")
                    
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            pass

    await redis_client.close()
    await engine.dispose()
    logger.info("Scheduler остановлен.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig.value)
    loop.run_until_complete(run())
