import jwt
from pwdlib import PasswordHash
from fastapi import HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.models.models import User

password_hash = PasswordHash.recommended()

async def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[int]:
    try:
        user_res = await session.execute(
            select(User.id, User.hashed_password, User.is_active)
            .where(User.email == email)
        )
        user_row = user_res.first()

        if not user_row:
            return None

        user_id, hashed_password, is_active = user_row

        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This user was deleted"
            )

        if not await verify_password(password, hashed_password):
            return None

        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation error: {str(e)}"
        )

async def logout_with_cookie(response: Response) -> None:
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False
    )