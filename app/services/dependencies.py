from fastapi import Depends, HTTPException, status, Cookie
from jwt.exceptions import InvalidTokenError
import jwt
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database.database import get_session
from app.models.models import User, UserRole

async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    access_token: str = Cookie(None)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    try:
        payload = jwt.decode(access_token, settings.SECRET, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    return user

async def get_current_manager(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user

async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user