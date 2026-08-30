import os
from sqlalchemy import BigInteger, String, DateTime, func, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shop.db")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[str] = mapped_column(String(50), nullable=False)
    receipt_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending_payment")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_or_update_user(telegram_id: int, username: str = "", full_name: str = ""):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            new_user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(new_user)
        else:
            user.username = username
            user.full_name = full_name
        await session.commit()

async def create_order(user_id: int, username: str, plan_name: str, price: str) -> int:
    async with async_session() as session:
        try:
            new_order = Order(
                user_id=user_id,
                username=username,
                plan_name=plan_name,
                price=str(price),
                status="pending_payment"
            )
            session.add(new_order)
            await session.commit()
            await session.refresh(new_order)
            return new_order.id
        except Exception as e:
            await session.rollback()
            print(f"❌ DATABASE ERROR in create_order: {e}")
            raise e
async def update_order_receipt(order_id: int, receipt_file_id: str):
    async with async_session() as session:
        await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(receipt_file_id=receipt_file_id, status="pending_config")
        )
        await session.commit()

async def set_order_completed(order_id: int, config_link: str):
    async with async_session() as session:
        await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(config_link=config_link, status="completed")
        )
        await session.commit()

async def get_order(order_id: int):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

async def get_user_orders(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == user_id, Order.status == "completed")
        )
        return result.scalars().all()

async def get_next_pending_order():
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.status == "pending_config")
            .order_by(Order.created_at.asc())
        )
        return result.scalars().first()

async def get_recent_completed_orders(limit: int = 10):
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.status == "completed")
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

async def count_pending_orders() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Order.id)).where(Order.status == "pending_config")
        )
        return result.scalar() or 0