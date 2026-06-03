import asyncio
import json
import logging
import os
import signal
import httpx
from redis.asyncio import Redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("parser")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
shutdown_event = asyncio.Event()

def handle_shutdown(sig: int) -> None:
    logger.info("Graceful Shutdown Parser...")
    shutdown_event.set()

async def fetch_moex_prices(tickers: list[str]) -> dict:
    tickers_str = ",".join(tickers)
    url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?securities={tickers_str}"
    
    prices = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            marketdata = data.get("marketdata", {})
            columns = marketdata.get("columns", [])
            rows = marketdata.get("data", [])
            
            if "SECID" in columns and "LAST" in columns:
                secid_idx = columns.index("SECID")
                last_idx = columns.index("LAST")
                
                for row in rows:
                    secid = row[secid_idx]
                    last_price = row[last_idx]
                    if last_price is not None:
                        prices[secid] = float(last_price)
    except Exception as e:
        logger.error(f"Ошибка при запросе к MOEX API: {e}")
        
    return prices

async def run():
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Parser запущен, ожидание очереди queue:parse")
    
    while not shutdown_event.is_set():
        try:
            task = await redis_client.brpop("queue:parse", timeout=1.0)
            if not task:
                continue
                
            _, message = task
            data = json.loads(message)
            tickers = data.get("tickers", [])
            
            if not tickers:
                continue
                
            logger.info(f"Парсинг цен для: {tickers}")
            prices = await fetch_moex_prices(tickers)
            
            if prices:
                logger.info(f"Успешно спарсено {len(prices)} цен. Отправка в analyzer.")
                await redis_client.lpush("queue:analyze", json.dumps({"prices": prices}))
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Ошибка в воркере Parser: {e}")

    await redis_client.close()
    logger.info("Parser остановлен.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, sig.value)
    loop.run_until_complete(run())
