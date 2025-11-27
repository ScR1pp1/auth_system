import asyncio
from sqlalchemy import select
from app.database.database import session_factory
from app.models.models import User, UserRole
from app.services.helpers import get_password_hash

async def create_test_users():
    async with session_factory() as session:
        try:
            existing_users = await session.execute(select(User).where(User.email.in_([
                "admin@example.com",
                "manager@example.com",
                "user@example.com"
            ])))

            existing_emails = [user.email for user in existing_users.scalars()]

            test_users = [
                {
                    "surname": "Adminov",
                    "name": "Admin",
                    "email": "admin@example.com",
                    "password": "admin123",
                    "role": UserRole.ADMIN
                },
                {
                    "surname": "Managerov",
                    "name": "Manager",
                    "email": "manager@example.com",
                    "password": "manager123",
                    "role": UserRole.MANAGER
                },
                {
                    "surname": "Userov",
                    "name": "User",
                    "email": "user@example.com",
                    "password": "user123",
                    "role": UserRole.USER
                }
            ]

            created_count = 0
            for user_data in test_users:
                if user_data["email"] not in existing_emails:
                    hashed_password = await get_password_hash(user_data["password"])

                    user = User(
                        surname=user_data["surname"],
                        name=user_data["name"],
                        email=user_data["email"],
                        hashed_password=hashed_password,
                        role=user_data["role"]
                    )

                    session.add(user)
                    created_count += 1
                    print(
                        f"User created: {user_data['email']} / {user_data['password']} ({user_data['role']})")

            if created_count > 0:
                await session.commit()
                print(f"\nTest users successfully created: {created_count} users")
            else:
                print("Test users already exists")

            return created_count

        except Exception as e:
            await session.rollback()
            print(f"Error while creating test users: {e}")
            return 0

if __name__ == "__main__":
    asyncio.run(create_test_users())