from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.service import BaseService
from . import models, schemas


class NotificationTemplateService(BaseService[models.NotificationTemplate]):
    def __init__(self):
        super().__init__(models.NotificationTemplate)

    async def create_template(
        self, db: AsyncSession, template: schemas.NotificationTemplateCreate
    ) -> models.NotificationTemplate:
        db_template = models.NotificationTemplate(**template.model_dump())
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        return db_template

    async def get_template_by_name(
        self, db: AsyncSession, name: str
    ) -> Optional[models.NotificationTemplate]:
        query = select(self.model).filter(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()


class NotificationSettingsService(BaseService[models.NotificationSettings]):
    def __init__(self):
        super().__init__(models.NotificationSettings)

    async def get_user_settings(
        self, db: AsyncSession, user_id: int
    ) -> Optional[models.NotificationSettings]:
        query = select(self.model).filter(self.model.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_settings(
        self, db: AsyncSession, settings: schemas.NotificationSettingsCreate, user_id: int
    ) -> models.NotificationSettings:
        db_settings = models.NotificationSettings(**settings.model_dump(), user_id=user_id)
        db.add(db_settings)
        await db.commit()
        await db.refresh(db_settings)
        return db_settings

    async def update_settings(
        self, db: AsyncSession, user_id: int, settings: schemas.NotificationSettingsUpdate
    ) -> Optional[models.NotificationSettings]:
        db_settings = await self.get_user_settings(db, user_id)
        if not db_settings:
            return None

        update_data = settings.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_settings, key, value)

        await db.commit()
        await db.refresh(db_settings)
        return db_settings


class NotificationService(BaseService[models.Notification]):
    def __init__(self):
        super().__init__(models.Notification)

    async def create_notification(
        self, db: AsyncSession, notification: schemas.NotificationCreate, user_id: int
    ) -> models.Notification:
        db_notification = models.Notification(
            **notification.model_dump(),
            user_id=user_id
        )
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        return db_notification

    async def get_pending_notifications(
        self, db: AsyncSession, limit: int = 100
    ) -> List[models.Notification]:
        query = (
            select(self.model)
            .filter(self.model.is_sent == False)
            .order_by(self.model.created_at)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def mark_as_sent(
        self, db: AsyncSession, notification_id: int, error_message: Optional[str] = None
    ) -> Optional[models.Notification]:
        notification = await self.get(db, notification_id)
        if not notification:
            return None

        notification.is_sent = True
        notification.sent_at = datetime.utcnow().isoformat()
        if error_message:
            notification.error_message = error_message

        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_user_notifications(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Notification]:
        query = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all() 