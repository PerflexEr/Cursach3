from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from services.auth.service import UserService
from services.auth.models import User
from . import schemas
from .service import (
    NotificationTemplateService,
    NotificationSettingsService,
    NotificationService,
)

app = FastAPI(title="Notification Service", version="1.0.0")

template_service = NotificationTemplateService()
settings_service = NotificationSettingsService()
notification_service = NotificationService()
user_service = UserService()


@app.post("/templates/", response_model=schemas.NotificationTemplate)
async def create_template(
    template: schemas.NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await template_service.create_template(db=db, template=template)


@app.get("/templates/", response_model=List[schemas.NotificationTemplate])
async def read_templates(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await template_service.get_all(db, skip=skip, limit=limit)


@app.get("/settings/me/", response_model=schemas.NotificationSettings)
async def read_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    settings = await settings_service.get_user_settings(db, current_user.id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@app.post("/settings/", response_model=schemas.NotificationSettings)
async def create_user_settings(
    settings: schemas.NotificationSettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    existing_settings = await settings_service.get_user_settings(db, current_user.id)
    if existing_settings:
        raise HTTPException(
            status_code=400,
            detail="Settings already exist"
        )
    return await settings_service.create_settings(
        db=db, settings=settings, user_id=current_user.id
    )


@app.put("/settings/me/", response_model=schemas.NotificationSettings)
async def update_user_settings(
    settings: schemas.NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    updated_settings = await settings_service.update_settings(
        db, current_user.id, settings
    )
    if not updated_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return updated_settings


@app.post("/notifications/", response_model=schemas.Notification)
async def create_notification(
    notification: schemas.NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем существование шаблона
    template = await template_service.get(db, notification.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return await notification_service.create_notification(
        db=db, notification=notification, user_id=current_user.id
    )


@app.get("/notifications/", response_model=List[schemas.Notification])
async def read_notifications(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await notification_service.get_user_notifications(
        db, current_user.id, skip=skip, limit=limit
    )


@app.get("/notifications/pending/", response_model=List[schemas.Notification])
async def read_pending_notifications(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await notification_service.get_pending_notifications(db, limit=limit) 