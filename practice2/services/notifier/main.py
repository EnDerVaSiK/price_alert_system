import asyncio
import json
import logging
import os
import signal
import httpx
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("notifier")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

shutdown_event = asyncio.Event()

def handle_shutdown(sig: int) -> None:
    logger.info("Graceful Shutdown Notifier...")
    shutdown_event.set()

async def run():
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Notifier запущен. Ожидание queue:notify")
    
    async with httpx.AsyncClient() as http_client:
        while not shutdown_event.is_set():
            try:
                task = await redis_client.brpop("queue:notify", timeout=1.0)
                if not task:
                    continue
                    
                _, message = task
                data = json.loads(message)
                
                chat_id = data.get("telegram_id")
                text = data.get("text")
                
                if not TELEGRAM_BOT_TOKEN:
                    logger.warning(f"Токен не задан. MOCK отправка {chat_id}:\n{text}")
                    continue
                
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                
                resp = await http_client.post(TELEGRAM_API_URL, json=payload, timeout=5.0)
                resp.raise_for_status()
                logger.info(f"Уведомление успешно отправлено пользователю {chat_id}")
                
            except httpx.HTTPError as e:
                logger.error(f"Ошибка сети при отправке в Telegram: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в Notifier: {e}")

    await redis_client.close()
    logger.info("Notifier остановлен.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig.value)
    loop.run_until_complete(run())
