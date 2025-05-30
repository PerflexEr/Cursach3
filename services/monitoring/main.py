from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from shared.database import get_db
from services.auth.service import UserService
from services.auth.models import User
from . import schemas
from .service import SensorService, MeasurementService, AlertService

app = FastAPI(title="Monitoring Service", version="1.0.0")

sensor_service = SensorService()
measurement_service = MeasurementService()
alert_service = AlertService()
user_service = UserService()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "monitoring"}


@app.post("/sensors/", response_model=schemas.Sensor)
async def create_sensor(
    sensor: schemas.SensorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await sensor_service.create_sensor(db=db, sensor=sensor, user_id=current_user.id)


@app.get("/hives/{hive_id}/sensors/", response_model=List[schemas.Sensor])
async def read_sensors(
    hive_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await sensor_service.get_sensors_by_hive(db, hive_id, current_user.id)


@app.get("/sensors/{sensor_id}/stats/", response_model=schemas.SensorStats)
async def read_sensor_stats(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    stats = await sensor_service.get_sensor_stats(db, sensor_id, current_user.id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return stats


@app.post("/measurements/", response_model=schemas.Measurement)
async def create_measurement(
    measurement: schemas.MeasurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем, что датчик принадлежит пользователю
    sensor = await sensor_service.get(db, measurement.sensor_id)
    if not sensor or sensor.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return await measurement_service.create_measurement(db=db, measurement=measurement)


@app.get("/sensors/{sensor_id}/measurements/", response_model=List[schemas.Measurement])
async def read_measurements(
    sensor_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем, что датчик принадлежит пользователю
    sensor = await sensor_service.get(db, sensor_id)
    if not sensor or sensor.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return await measurement_service.get_measurements_by_sensor(
        db, sensor_id, start_date, end_date, limit
    )


@app.post("/alerts/", response_model=schemas.Alert)
async def create_alert(
    alert: schemas.AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем, что датчик и улей принадлежат пользователю
    sensor = await sensor_service.get(db, alert.sensor_id)
    if not sensor or sensor.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return await alert_service.create_alert(db=db, alert=alert, user_id=current_user.id)


@app.get("/alerts/", response_model=List[schemas.Alert])
async def read_alerts(
    hive_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    return await alert_service.get_active_alerts(db, current_user.id, hive_id)


@app.put("/alerts/{alert_id}/resolve/", response_model=schemas.Alert)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    alert = await alert_service.resolve_alert(db, alert_id, current_user.id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert