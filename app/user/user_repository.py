# user repository
from app.database.base_repository import BaseRepository
from app.user.user_schema import UserCreate
from sqlalchemy import select, update, func, exists
from app.database.models.user import User as UserModel
from app.database.models.user import Account
from app.user.user_schema import AccountCreate
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_user(self, user_in: UserModel) -> UserModel:
        try:
            self.db.add(user_in)
            await self.db.commit()
            await self.db.refresh(user_in)
            return user_in
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"IntegrityError: User creation failed: {e}")
            #  More specific error message
            raise ValueError(
                "User creation failed: Email or username might already be in use.") from e
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemyError: User creation failed: {e}")
            raise ValueError(
                "User creation failed due to a database error.") from e

    async def user_exist_by_email(self, email: str) -> bool:
        try:
            query = exists().where(func.lower(UserModel.email) == email.lower())
            result = await self.db.execute(select(query))
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error checking user existence: {e}")
            raise ValueError(f"Database error while checking user existence.") from e
        

    async def get_user_by_email(self, email: str) -> UserModel:
        try:
            query = select(UserModel).where(UserModel.email == email)
            result = await self.db.execute(query)
            return result.scalar_one()  # Raises NoResultFound or MultipleResultsFound
        except NoResultFound:
            logger.warning(f"No user found with email: {email}")
            raise ValueError(f"No user found with email: {email}")
        except MultipleResultsFound:
            logger.error(f"Multiple users found with email: {email}")
            raise ValueError(f"Multiple users found with email: {email}")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error fetching user by email: {e}")
            raise ValueError(
                f"Database error while fetching user by email.") from e

    async def get_user_by_id(self, user_id: str):
        try:

            query = select(UserModel).where(UserModel.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                logger.warning(f"No User found with ID {user_id}")
            return user
        except ValueError:
            # Handle case where user_id can't be converted to int
            logger.error(f"Invalid user ID format: {user_id}")
            # Raise, don't return None.
            raise ValueError(f"Invalid user ID format: {user_id}")
        except NoResultFound:
            # Log the specific error
            logger.warning(f"No user found with ID: {user_id}")
            # Raise, so calling function handles.
            raise ValueError(f"No user found with ID: {user_id}")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error fetching user by ID: {e}")
            raise ValueError(
                f"Database error while fetching user by ID.") from e

    async def get_account_by_provider(self, provider_account_id: int, provider: str):
        try:
            query = select(Account).where(
                Account.provider_account_id == provider_account_id, Account.provider == provider)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()  # Returns None if not found
        except SQLAlchemyError as e:
            logger.error(
                f"SQLAlchemyError: Error fetching account by provider: {e}")
            raise ValueError(
                f"Database error while fetching account by provider.") from e

    async def get_user_from_account(self, account: Account) -> UserModel:
        try :
            query = select(UserModel).filter(UserModel.id == account.user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise ValueError(
                f"Database error while fetching user from account.") from e


    async def create_account(self, account_data: AccountCreate) -> Account:
        try:
            new_account = Account(
                provider=account_data.provider,
                provider_account_id=account_data.provider_account_id,
                user_id=account_data.user_id
            )
            self.db.add(new_account)
            await self.db.commit()
            await self.db.refresh(new_account)
            return new_account
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"SQLAlchemyError: Error creating account: {e}")
            raise ValueError(
                f"Database error while creating account.") from e

    async def verify_user(self, user_id: str) -> bool:
        try:
            # This will raise if ID invalid
            user = await self.get_user_by_id(user_id)
            if not user:
                return False  # Should not get here, get_user_by_id now raises

            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            await self.db.commit()
            return True

        except ValueError as e:  # Catch ValueError from get_user_by_id
            logger.error(f"ValueError in verify_user: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error verifying user: {e}")
            raise ValueError(f"Database error while verifying user") from e

    async def get_user_by_verification_token(self, token: str) -> UserModel:
        try:
            query = select(UserModel).where(
                UserModel.verification_token == token,
                UserModel.verification_token_expires > datetime.now(
                    timezone.utc)
            )
            result = await self.db.execute(query)
            return result.scalar_one()  # Raises NoResultFound or MultipleResultsFound
        except NoResultFound:
            logger.warning(f"No user found with verification token: {token}")
            raise ValueError(f"No user found with verification token: {token}")
        except SQLAlchemyError as e:
            logger.error(
                f"SQLAlchemyError: Error fetching user by verification token: {e}")
            raise ValueError(f"Database error while fetching user")

    async def get_user_by_reset_token(self, token: str) -> UserModel:
        try:
            query = select(UserModel).where(
                UserModel.reset_password_token == token,
                UserModel.reset_password_expires > datetime.now(timezone.utc)
            )
            result = await self.db.execute(query)
            return result.scalar_one()  # Raises NoResultFound or MultipleResultsFound
        except NoResultFound:
            logger.warning(f"No user found with reset token: {token}")
            raise ValueError(f"No user found with reset token: {token}")
        except SQLAlchemyError as e:
            logger.error(
                f"SQLAlchemyError: Error fetching user by reset token: {e}")
            raise ValueError(
                f"Database error while fetching user by reset token.") from e

    async def update_user(self, user_id: str, user_update: UserCreate) -> UserModel:
        try:
            # Raises if not found or id invalid
            user = await self.get_user_by_id(user_id)
            # if not user:  # Redundant:  get_user_by_id raises
            #     raise ValueError(f"No user found with ID: {user_id}")

            stmt = (
                update(UserModel)
                # Use user.id, it's already an integer
                .where(UserModel.id == user.id)
                # Use dict and exclude unset
                .values(**user_update.dict(exclude_unset=True))
                .returning(UserModel)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            updated_user = result.scalar_one()  # Correctly handle the result
            # Refresh after commit, with correct user
            await self.db.refresh(updated_user)
            return updated_user

        except ValueError as e:
            logger.error(f"ValueError: {e}")  # More specific logging
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error updating user: {e}")
            raise ValueError(f"Database error while updating user.") from e
        except Exception as e:  # Catch other potential errors.
            logger.exception(f"Unexpected error updating user: {e}")
            raise

    async def delete_user(self, user_id: str) -> bool:
        try:
            # Raises if not found or id invalid
            user = await self.get_user_by_id(user_id)
            # if not user: # Redundant
            #     raise ValueError(f"No user found with ID: {user_id}")

            await self.db.delete(user)
            await self.db.commit()
            return True

        except ValueError as e:  # More specific error handling
            logger.error(f"ValueError: {e}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError: Error deleting user: {e}")
            raise ValueError(f"Database error while deleting user.") from e
        except Exception as e:  # Catch any other exceptions
            logger.exception(f"Unexpected error deleting user: {e}")
            raise
