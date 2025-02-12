from app.database.base_repository import BaseRepository
from app.users.user_schema import UserCreate
from sqlalchemy import select
from app.database.models.user import User as UserModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, NoResultFound, MultipleResultsFound


class UserRepository(BaseRepository):
    async def create(self, user_in: UserCreate) -> UserModel:
        new_user = UserModel(**user_in.model_dump(exclude_none=True))
        self.db.add(new_user)

        try:
            await self.db.commit()
            await self.db.refresh(new_user)
            new_user.id = str(new_user.id)  # Convert id to string
            return new_user

        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(
                "User creation failed due to a database constraint violation") from e

    async def user_exist_by_email(self, email: str) -> bool:
        try:
            query = select(UserModel).where(UserModel.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            print("this a user from the repository")
            print(user)
            return bool(user)
        except SQLAlchemyError as e:
            # Log the error and re-raise or handle it appropriately
            raise ValueError(
                f"Database error while checking user existence: {e}") from e

    async def get_user_by_email(self, email: str) -> UserModel:
        try:
            query = select(UserModel).where(UserModel.email == email)
            result = await self.db.execute(query)
            return result.scalar_one()  # Raises NoResultFound or MultipleResultsFound
        except NoResultFound:
            raise ValueError(f"No user found with email: {email}")
        except MultipleResultsFound:
            raise ValueError(f"Multiple users found with email: {email}")
        except SQLAlchemyError as e:
            raise ValueError(
                f"Database error while fetching user by email: {e}") from e

    async def get_user_by_id(self, user_id: str) -> UserModel:
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one()  # Raises NoResultFound or MultipleResultsFound
        except NoResultFound:
            raise ValueError(f"No user found with ID: {user_id}")
        except MultipleResultsFound:
            raise ValueError(f"Multiple users found with ID: {user_id}")
        except SQLAlchemyError as e:
            raise ValueError(
                f"Database error while fetching user by ID: {e}") from e
