from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from fastapi import HTTPException, status
from app.models.models import User

class UserService:
    @classmethod
    async def update_user_data(cls, session: AsyncSession, user_id: int, update_fields: dict):
        try:
            stmt = update(User).where(User.id == user_id).values(**update_fields)
            await session.execute(stmt)
            await session.commit()

            updated_user = await cls.get_user_by_id(session, user_id)
            return {"message": "successfully updated", "user": updated_user}
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @classmethod
    async def get_user_by_email(cls, session: AsyncSession, email: str):
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_user_by_id(cls, session: AsyncSession, user_id: int):
        return await session.get(User, user_id)

    @classmethod
    async def soft_remove(cls, session: AsyncSession, user: User):
        try:
            stmt = update(User).where(User.id == user.id).values(is_active=False)
            await session.execute(stmt)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        return {"message": "successfully removed"}

    @classmethod
    async def real_delete(cls, session: AsyncSession, user: User):
        try:
            await session.delete(user)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

    @classmethod
    async def add_one(cls, session: AsyncSession, user: User):
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
            raise e

    @classmethod
    async def get_all_users(cls, session: AsyncSession):
        stmt = select(User)
        result = await session.execute(stmt)
        return result.scalars().all()