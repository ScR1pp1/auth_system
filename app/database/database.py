from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

DATABASE_URL = settings.get_db_url()

engine = create_async_engine(url=DATABASE_URL)
session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables successfully created via create_tables")
