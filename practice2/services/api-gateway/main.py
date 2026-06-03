import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
)
from sqlalchemy import select, delete

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import AsyncSessionLocal, User, Ticker, Subscription, Base, engine

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api-gateway")

# Инициализация Telegram-бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

POPULAR_TICKERS = ["SBER", "GAZP", "YDEX", "LKOH", "ROSN"]

# --- КЛАВИАТУРЫ ---
def get_inline_keyboard():
    buttons = [[InlineKeyboardButton(text=f"📊 {t}", callback_data=f"sub_{t}")] for t in POPULAR_TICKERS]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Выбрать акции"), KeyboardButton(text="📋 Мои подписки")],
            [KeyboardButton(text="🗑 Отписаться от всего")] 
        ],
        resize_keyboard=True,
        is_persistent=True
    )

# --- ХЭНДЛЕРЫ TELEGRAM-БОТА ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            user = User(telegram_id=tg_id)
            session.add(user)
            await session.commit()
            logger.info(f"Зарегистрирован новый пользователь: {tg_id}")
            
    await message.answer(
        "👋 Добро пожаловать в MOEX Price Alert!\n\nИспользуйте меню внизу экрана, чтобы управлять вашим портфелем отслеживания.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📈 Выбрать акции")
async def show_catalog(message: Message):
    await message.answer("Выберите акции (нажмите повторно для отписки):", reply_markup=get_inline_keyboard())

@dp.message(F.text == "📋 Мои подписки")
async def show_subs(message: Message):
    tg_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            await message.answer("Вы не зарегистрированы. Нажмите /start")
            return
        
        stmt = select(Ticker.symbol, Subscription.last_notified_price)\
            .join(Subscription).where(Subscription.user_id == user.id)
        result = await session.execute(stmt)
        subs = result.all()
        
        if not subs:
            await message.answer("У вас пока нет активных подписок 📭\nИспользуйте кнопку «📈 Выбрать акции».")
            return
            
        text = "<b>Ваши текущие подписки:</b>\n\n"
        for symbol, price in subs:
            price_str = f"{price} ₽" if price else "<i>Ожидание первой цены...</i>"
            text += f"🔹 <b>{symbol}</b> (Посл. цена: {price_str})\n"
            
        await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "🗑 Отписаться от всего")
async def delete_all_subs(message: Message):
    tg_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            await message.answer("Вы не зарегистрированы. Нажмите /start")
            return

        stmt = delete(Subscription).where(Subscription.user_id == user.id)
        result = await session.execute(stmt)
        await session.commit()
        
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            logger.info(f"Пользователь {tg_id} удалил все свои подписки ({deleted_count} шт).")
            await message.answer(f"✅ Вы успешно отписались от всех активов ({deleted_count} шт).")
        else:
            await message.answer("📭 У вас и так нет активных подписок.")

@dp.callback_query(F.data.startswith("sub_"))
async def process_subscription(callback: CallbackQuery):
    ticker_symbol = callback.data.split("_")[1]
    tg_id = callback.from_user.id
    
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            await callback.answer("Ошибка: пользователь не найден /start", show_alert=True)
            return

        ticker = await session.scalar(select(Ticker).where(Ticker.symbol == ticker_symbol))
        if not ticker:
            ticker = Ticker(symbol=ticker_symbol)
            session.add(ticker)
            await session.commit()
            await session.refresh(ticker)

        sub = await session.scalar(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.ticker_id == ticker.id)
        )
        
        if sub:
            await session.delete(sub)
            await session.commit()
            logger.info(f"Пользователь {tg_id} отписался от {ticker_symbol}")
            await callback.message.answer(f"❌ Вы отписались от обновлений <b>{ticker_symbol}</b>.", parse_mode="HTML")
        else:
            new_sub = Subscription(user_id=user.id, ticker_id=ticker.id)
            session.add(new_sub)
            await session.commit()
            logger.info(f"Пользователь {tg_id} подписался на {ticker_symbol}")
            await callback.message.answer(f"✅ Вы успешно подписались на <b>{ticker_symbol}</b>.", parse_mode="HTML")
            
        await callback.answer()

# --- FASTAPI И УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте API Gateway: создаем таблицы и запускаем бота
    logger.info("Проверка/создание таблиц в БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Запуск Telegram-бота (aiogram) в фоновом режиме...")
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    yield # Сервер работает
    
    # При остановке API Gateway: корректно глушим бота
    logger.info("Остановка Telegram-бота...")
    polling_task.cancel()
    await bot.session.close()
    await engine.dispose()

# Инициализируем FastAPI
app = FastAPI(title="Admin API", lifespan=lifespan)

# Разрешаем запросы с нашего React Frontend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Для локальной разработки разрешаем всё
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REST API ЭНДПОИНТЫ ---
@app.get("/api/v1/health")
async def health_check():
    """Эндпоинт для проверки жизнеспособности сервиса (Liveness probe)"""
    return {"status": "ok", "service": "api-gateway"}

@app.get("/api/v1/stats")
async def get_stats():
    """Эндпоинт для админ-панели: отдает статистику системы"""
    async with AsyncSessionLocal() as session:
        # Подсчет количества пользователей
        users_result = await session.execute(select(User))
        users_count = len(users_result.all())
        
        # Подсчет количества подписок
        subs_result = await session.execute(select(Subscription))
        subs_count = len(subs_result.all())
        
        return {
            "total_users": users_count, 
            "total_subscriptions": subs_count
        }

if __name__ == "__main__":
    # Запускаем FastAPI сервер (uvicorn), который сам поднимет Telegram-бота через lifespan
    uvicorn.run(app, host="0.0.0.0", port=8000)
