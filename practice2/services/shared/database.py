import os
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, DateTime, String, Float

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/price_alerts")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    
    subscriptions = relationship("Subscription", back_populates="user")

class Ticker(Base):
    __tablename__ = 'tickers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String, unique=True, index=True)
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    subscriptions = relationship("Subscription", back_populates="ticker")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    ticker_id: Mapped[int] = mapped_column(ForeignKey('tickers.id'))
    last_notified_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    user = relationship("User", back_populates="subscriptions")
    ticker = relationship("Ticker", back_populates="subscriptions")
