from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_session
from app.models.models import User
from app.schemas.schemas import UserLogin, UserShow, UserRegister
from app.services.UserService import UserService
from app.services.dependencies import get_current_user
from app.services.helpers import create_access_token, authenticate_user, get_password_hash, logout_with_cookie

router = APIRouter(tags=["Personal account"])

@router.post('/registration', response_model=UserShow)
async def registration(
        user_data: UserRegister,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    curr_user = await UserService.get_user_by_email(session=session, email=user_data.email)

    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    try:
        if curr_user is not None:
            if curr_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered. Try to login."
                )
            else:
                await UserService.real_delete(session=session, user=curr_user)

        hashed_password = await get_password_hash(user_data.password)
        new_user = User(
            surname=user_data.surname,
            name=user_data.name,
            middle_name=user_data.middle_name,
            email=user_data.email,
            hashed_password=hashed_password
        )

        await UserService.add_one(session=session, user=new_user)
        return UserShow(
            surname=new_user.surname,
            name=new_user.name,
            middle_name=user_data.middle_name,
            email=new_user.email,
            role=new_user.role
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login")
async def login(
        form: UserLogin,
        session: Annotated[AsyncSession, Depends(get_session)],
        response: Response
):
    user_id = await authenticate_user(session=session, **form.model_dump())

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = await create_access_token(data={"sub": str(user_id)})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=24 * 60 * 60,
        secure=False
    )
    return {"message": "Successfully logged in"}

@router.post("/logout")
async def logout(
        current_user: Annotated[User, Depends(get_current_user)],
        response: Response
):
    await logout_with_cookie(response)
    return {"message": "Successfully logged out"}