from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.service import BaseService
from . import models, schemas


class SensorService(BaseService[models.Sensor]):
    def __init__(self):
        super().__init__(models.Sensor)

    async def create_sensor(
        self, db: AsyncSession, sensor: schemas.SensorCreate, user_id: int
    ) -> models.Sensor:
        db_sensor = models.Sensor(**sensor.model_dump(), user_id=user_id)
        db.add(db_sensor)
        await db.commit()
        await db.refresh(db_sensor)
        return db_sensor

    async def get_sensors_by_hive(
        self, db: AsyncSession, hive_id: int, user_id: int
    ) -> List[models.Sensor]:
        query = (
            select(self.model)
            .filter(self.model.hive_id == hive_id)
            .filter(self.model.user_id == user_id)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_sensor_stats(
        self, db: AsyncSession, sensor_id: int, user_id: int
    ) -> Optional[schemas.SensorStats]:
        # Get sensor
        sensor_query = (
            select(self.model)
            .filter(self.model.id == sensor_id)
            .filter(self.model.user_id == user_id)
        )
        sensor_result = await db.execute(sensor_query)
        sensor = sensor_result.scalar_one_or_none()

        if not sensor:
            return None

        # Get latest measurement and statistics
        stats_query = (
            select(
                func.max(models.Measurement.value).label("last_value"),
                func.min(models.Measurement.value).label("min_value"),
                func.max(models.Measurement.value).label("max_value"),
                func.avg(models.Measurement.value).label("avg_value"),
                func.max(models.Measurement.battery_level).label("battery_level"),
                func.max(models.Measurement.created_at).label("last_measurement_time"),
            )
            .filter(models.Measurement.sensor_id == sensor_id)
        )
        stats_result = await db.execute(stats_query)
        stats = stats_result.one()

        return schemas.SensorStats(
            sensor_id=sensor.id,
            sensor_name=sensor.name,
            sensor_type=sensor.sensor_type,
            last_value=stats.last_value,
            min_value=stats.min_value,
            max_value=stats.max_value,
            avg_value=stats.avg_value,
            battery_level=stats.battery_level,
            last_measurement_time=stats.last_measurement_time,
        )


class MeasurementService(BaseService[models.Measurement]):
    def __init__(self):
        super().__init__(models.Measurement)

    async def create_measurement(
        self, db: AsyncSession, measurement: schemas.MeasurementCreate
    ) -> models.Measurement:
        db_measurement = models.Measurement(**measurement.model_dump())
        db.add(db_measurement)
        await db.commit()
        await db.refresh(db_measurement)
        return db_measurement

    async def get_measurements_by_sensor(
        self,
        db: AsyncSession,
        sensor_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[models.Measurement]:
        query = select(self.model).filter(self.model.sensor_id == sensor_id)

        if start_date:
            query = query.filter(self.model.created_at >= start_date)
        if end_date:
            query = query.filter(self.model.created_at <= end_date)

        query = query.order_by(self.model.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


class AlertService(BaseService[models.Alert]):
    def __init__(self):
        super().__init__(models.Alert)

    async def create_alert(
        self, db: AsyncSession, alert: schemas.AlertCreate, user_id: int
    ) -> models.Alert:
        db_alert = models.Alert(**alert.model_dump(), user_id=user_id)
        db.add(db_alert)
        await db.commit()
        await db.refresh(db_alert)
        return db_alert

    async def get_active_alerts(
        self, db: AsyncSession, user_id: int, hive_id: Optional[int] = None
    ) -> List[models.Alert]:
        query = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .filter(self.model.is_resolved == False)
        )

        if hive_id:
            query = query.filter(self.model.hive_id == hive_id)

        query = query.order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def resolve_alert(
        self, db: AsyncSession, alert_id: int, user_id: int
    ) -> Optional[models.Alert]:
        alert = await self.get(db, alert_id)
        if not alert or alert.user_id != user_id:
            return None

        alert.is_resolved = True
        alert.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)
        return alert 