import asyncio
import json
import logging
import os
import signal
import sys
from redis.asyncio import Redis
from sqlalchemy.future import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import AsyncSessionLocal, Ticker, Subscription, User, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("analyzer")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
shutdown_event = asyncio.Event()

def handle_shutdown(sig: int) -> None:
    logger.info("Graceful Shutdown Analyzer...")
    shutdown_event.set()

async def run():
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Analyzer запущен. Ожидание queue:analyze")
    
    while not shutdown_event.is_set():
        try:
            task = await redis_client.brpop("queue:analyze", timeout=1.0)
            if not task:
                continue
                
            _, message = task
            prices = json.loads(message).get("prices", {})
            
            async with AsyncSessionLocal() as session:
                for symbol, current_price in prices.items():
                    # 1. Находим тикер и обновляем его общую цену
                    ticker = await session.scalar(select(Ticker).where(Ticker.symbol == symbol))
                    if not ticker: continue
                    ticker.last_price = current_price
                    
                    # 2. Находим всех подписчиков этого тикера
                    stmt = select(Subscription, User.telegram_id).join(User).where(Subscription.ticker_id == ticker.id)
                    subs_result = await session.execute(stmt)
                    
                    for sub, tg_id in subs_result:
                        old_price = sub.last_notified_price
                        
                        if old_price is None:
                            # Первая полученная цена для пользователя
                            sub.last_notified_price = current_price
                            logger.info(f"Первая цена {symbol} для пользователя {tg_id}: {current_price} RUB")
                            await redis_client.lpush("queue:notify", json.dumps({
                                "telegram_id": tg_id,
                                "text": f"📈 Вы начали отслеживать <b>{symbol}</b>.\nТекущая цена: <b>{current_price} ₽</b>"
                            }))
                            
                        elif old_price != current_price:
                            # Цена изменилась
                            delta = current_price - old_price
                            direction = "🟢 Выросла" if delta > 0 else "🔴 Упала"
                            sub.last_notified_price = current_price
                            
                            logger.info(f"Цена {symbol} для {tg_id} ИЗМЕНИЛАСЬ: {old_price} -> {current_price}")
                            await redis_client.lpush("queue:notify", json.dumps({
                                "telegram_id": tg_id,
                                "text": f"{direction}!\n\nАкция: <b>{symbol}</b>\nСтарая цена: <s>{old_price} ₽</s>\nНовая цена: <b>{current_price} ₽</b>\nИзменение: {delta:+.2f} ₽"
                            }))
                            
                await session.commit()
                        
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Ошибка в Analyzer: {e}")

    await redis_client.close()
    await engine.dispose()
    logger.info("Analyzer остановлен.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig.value)
    loop.run_until_complete(run())
