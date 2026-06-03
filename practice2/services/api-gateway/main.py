import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
)
from sqlalchemy import select, delete

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.database import AsyncSessionLocal, User, Ticker, Subscription, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api-gateway")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

POPULAR_TICKERS = ["SBER", "GAZP", "YDEX", "LKOH", "ROSN"]

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

async def main():
    logger.info("Проверка/создание таблиц в БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    logger.info("Запуск Telegram-бота (api-gateway)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())