from contextlib import asynccontextmanager
from typing import Annotated, List
from fastapi import FastAPI, Depends, Query, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.routers import router
from app.database.database import get_session, engine, Base
from app.models.models import User, UserRole
from app.schemas.schemas import UserShow, UserOwnUpdate, UserManagerShow, UserUpdate
from app.services.UserService import UserService
from app.services.dependencies import get_current_user, get_current_manager, get_current_admin
from app.services.helpers import verify_password, logout_with_cookie
from app.test_data import create_test_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("All tables are created/checked via lifespan")
    except Exception as e:
        print(f"Error while creating tables: {e}")

    try:
        await create_test_users()
    except Exception as e:
        print(f"Error while creating test data: {e}")
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router)

@app.get("/user/profile", response_model=UserShow, tags=["General"])
async def get_me(current_user : Annotated[User, Depends(get_current_user)]):
    return current_user

@app.put("/user/profile/update", tags=["General"])
async def update_me(update_data : UserOwnUpdate,
    current_user : Annotated[User, Depends(get_current_user)],
    session : Annotated[AsyncSession, Depends(get_session)],
    password: str = Query(
        json_schema_extra={"format": "password"},
        description="Enter your password",
        default=None
    )
):
    print()
    response = {"User" : UserShow(**current_user.__dict__), "details" : []}

    update_fields = update_data.model_dump(exclude_defaults=True)

    if not update_fields:
        print("There is nothing to change\n")

        response["details"].append("There is nothing to change")
        return response

    has_email = update_fields.get("email", None)
    if has_email is not None and current_user.email != has_email:
        if password is not None:
            if await verify_password(password, current_user.hashed_password):
                us_email = await UserService.get_user_by_email(session, current_user.email)

                if us_email is not None:
                    response["details"].append("This email address is already in use")
                    update_fields.pop("email")
            else:
                response["details"].append("Invalid password")
                update_fields.pop("email")
        else:
            response["details"].append("Enter your password")
            update_fields.pop("email")

    if update_fields:
        await UserService.update_user_data(session, current_user.id, update_fields)
        response["details"].append("successfully updated")

    response["User"] = UserShow(**current_user.__dict__)
    return response

@app.delete("/user/delete", tags=["General"])
async def delete_me(current_user : Annotated[User, Depends(get_current_user)], session : Annotated[AsyncSession, Depends(get_session)], response: Response):
    await UserService.soft_remove(session, current_user)
    await logout_with_cookie(response)
    return {"message" : "successfully deleted"}

@app.get("/users/get", response_model=List[UserManagerShow], tags = ["Managers only"])
async def get_users(current_user : Annotated[User, Depends(get_current_manager)], session : Annotated[AsyncSession, Depends(get_session)]):
    result = await UserService.get_all_users(session = session)
    return result

@app.put("/user/update/{user_id}", tags = ["Managers only"])
async def update_user_info(current_user : Annotated[User,
    Depends(get_current_manager)],
    session : Annotated[AsyncSession, Depends(get_session)],
    user_id : int, update_user_data : UserUpdate
):
    update_fields = update_user_data.model_dump(exclude_defaults=True)

    updated_user = await UserService.get_user_by_id(session, user_id=user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found"
        )

    if not current_user.role <= updated_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )

    if not update_fields:
        return {"message" : "There is nothing to change"}

    response = await UserService.update_user_data(session, updated_user.id, update_fields)
    return response

@app.get("/user/get/{user_id}", response_model=UserManagerShow, tags = ["Managers only"])
async def get_user(current_user : Annotated[User, Depends(get_current_manager)], session : Annotated[AsyncSession, Depends(get_session)],
                   user_id : int):
    result = await UserService.get_user_by_id(session, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found"
        )
    return result

@app.put("/user/put/{user_id}", tags = ["Admins only"])
async def set_role_to_user(current_user : Annotated[User, Depends(get_current_admin)], session : Annotated[AsyncSession, Depends(get_session)], user_id : int, role : UserRole):
    updated_user = await UserService.get_user_by_id(session, user_id=user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found"
        )

    if role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only set user or manager roles"
        )

    if current_user.role == updated_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can not demote other admins"
        )

    response = await UserService.update_user_data(session, user_id=user_id, update_fields={"role" : role})
    return response

@app.delete("/user/delete/{user_id}", tags = ["Admins only"])
async def delete_user(current_user : Annotated[User, Depends(get_current_admin)], session : Annotated[AsyncSession, Depends(get_session)],
                      user_id : int):
    deleted_user = await UserService.get_user_by_id(session, user_id=user_id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found"
        )

    if current_user.role == deleted_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can not delete other admins"
        )

    response = await UserService.soft_remove(session, user=deleted_user)
    return response

@app.get("/admin-check", tags=["Check Roles"])
async def check_admin(current_user : Annotated[User, Depends(get_current_admin)]):
    return {"MSG" : f"Hello, {current_user.name}! Your current role is {current_user.role}"}

@app.get("/manager-check", tags=["Check Roles"])
async def check_manager(current_user : Annotated[User, Depends(get_current_manager)]):
    return {"MSG" : f"Hello, {current_user.name}! Your current role is {current_user.role}"}

@app.get("/all-user")
async def all_user(session : Annotated[AsyncSession, Depends(get_session)]):
    result = await UserService.get_all_users(session)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)