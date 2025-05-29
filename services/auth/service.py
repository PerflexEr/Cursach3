from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.service import BaseService
from . import models, schemas, security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserService(BaseService[models.User]):
    def __init__(self):
        super().__init__(models.User)

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[models.User]:
        query = select(self.model).filter(self.model.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[models.User]:
        query = select(self.model).filter(self.model.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user: schemas.UserCreate) -> models.User:
        hashed_password = security.get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> Optional[models.User]:
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user

    async def get_current_user(
        self,
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
    ) -> models.User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        token_data = security.verify_token(token)
        if token_data is None:
            raise credentials_exception
            
        user = await self.get_user_by_username(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def update_user(
        self, db: AsyncSession, user_id: int, user_update: schemas.UserUpdate
    ) -> Optional[models.User]:
        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = security.get_password_hash(update_data.pop("password"))
        
        return await super().update(db, user_id, **update_data) 