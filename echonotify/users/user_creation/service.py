from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from echonotify.auth.schema import UserLoginSchema
from echonotify.auth.service import AuthService
from echonotify.exception import UserAlreadyExistsError
from echonotify.users.user_creation.repository import UserRepository
from echonotify.users.user_creation.schema import UserCreateSchema


class UserService:
    """Service class for handling user-related business logic."""

    def __init__(self, session: AsyncSession):
        """Initialize the service with a database session."""
        self.session = session
        self.user_repo = UserRepository(session)
        self.auth_service = AuthService()

    async def create_user(
        self, user_data: UserCreateSchema
    ) -> UserLoginSchema:
        """Create a new user with the provided data."""
        if await self.user_repo.user_exists(user_data.email):
            raise UserAlreadyExistsError()

        hashed_password = self.auth_service.hash_password(user_data.password)

        user = await self.user_repo.create_user_with_defaults(
            email=user_data.email,
            name=user_data.name,
            password=hashed_password,
        )

        access_token = self.auth_service.generate_access_token(
            user.id, user.email
        )
        refresh_token = await self.refresh_token_repo.generate_or_update_token(
            user.id
        )

        await self.session.commit()

        return UserLoginSchema(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def get_user_by_id(self, user_id: int):
        """Retrieve a user by their ID."""
        return await self.user_repo.get_user_by_id(user_id)

    async def update_user_password(
        self, email: str, new_password: str
    ) -> None:
        """Update a user's password."""
        hashed_password = self.auth_service.hash_password(new_password)
        try:
            await self.user_repo.update_user_password(email, hashed_password)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e


class CreateUser(UserService):
    async def create_user_service(
        self,
        user_data: UserCreateSchema,
    ) -> UserLoginSchema:
        """Legacy function, prefer using UserService class."""
        return await self.create_user(user_data)
