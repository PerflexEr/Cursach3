from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.service import BaseService
from . import models, schemas


class HiveService(BaseService[models.Hive]):
    def __init__(self):
        super().__init__(models.Hive)

    async def create_hive(
        self, db: AsyncSession, hive: schemas.HiveCreate, user_id: int
    ) -> models.Hive:
        db_hive = models.Hive(**hive.model_dump(), user_id=user_id)
        db.add(db_hive)
        await db.commit()
        await db.refresh(db_hive)
        return db_hive

    async def get_hives_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Hive]:
        query = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_hive_with_stats(
        self, db: AsyncSession, hive_id: int, user_id: int
    ) -> Optional[dict]:
        # Get hive with inspections
        query = (
            select(self.model)
            .filter(self.model.id == hive_id)
            .filter(self.model.user_id == user_id)
            .options(selectinload(self.model.inspections))
        )
        result = await db.execute(query)
        hive = result.scalar_one_or_none()

        if not hive:
            return None

        # Calculate statistics
        stats_query = (
            select(
                func.avg(models.Inspection.temperature).label("avg_temperature"),
                func.avg(models.Inspection.humidity).label("avg_humidity"),
                func.avg(models.Inspection.weight).label("avg_weight"),
                func.max(models.Inspection.created_at).label("last_inspection_date"),
            )
            .filter(models.Inspection.hive_id == hive_id)
        )
        stats_result = await db.execute(stats_query)
        stats = stats_result.one()

        # Create response dictionary
        inspections = [
            {
                "id": inspection.id,
                "hive_id": inspection.hive_id,
                "temperature": inspection.temperature,
                "humidity": inspection.humidity,
                "weight": inspection.weight,
                "notes": inspection.notes,
                "user_id": inspection.user_id,
                "created_at": inspection.created_at,
                "updated_at": inspection.updated_at
            }
            for inspection in hive.inspections
        ]

        return {
            "id": hive.id,
            "name": hive.name,
            "location": hive.location,
            "description": hive.description,
            "status": hive.status,  # Убираем .value, просто используем строку
            "queen_year": hive.queen_year,
            "frames_count": hive.frames_count,
            "user_id": hive.user_id,
            "created_at": hive.created_at,
            "updated_at": hive.updated_at,
            "inspections": inspections,
            "avg_temperature": stats.avg_temperature,
            "avg_humidity": stats.avg_humidity,
            "avg_weight": stats.avg_weight,
            "last_inspection_date": stats.last_inspection_date
        }


class InspectionService(BaseService[models.Inspection]):
    def __init__(self):
        super().__init__(models.Inspection)

    async def create_inspection(
        self, db: AsyncSession, inspection: schemas.InspectionCreate, user_id: int
    ) -> models.Inspection:
        db_inspection = models.Inspection(
            **inspection.model_dump(),
            user_id=user_id
        )
        db.add(db_inspection)
        await db.commit()
        await db.refresh(db_inspection)
        return db_inspection

    async def get_inspections_by_hive(
        self, db: AsyncSession, hive_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Inspection]:
        query = (
            select(self.model)
            .filter(self.model.hive_id == hive_id)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all() 