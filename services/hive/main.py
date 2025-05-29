from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from services.auth.service import UserService
from services.auth.models import User
from . import schemas
from .service import HiveService, InspectionService

app = FastAPI(title="Hive Service", version="1.0.0")

hive_service = HiveService()
inspection_service = InspectionService()
user_service = UserService()


@app.post("/hives/", response_model=schemas.HiveResponse)
async def create_hive(
    hive: schemas.HiveCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    db_hive = await hive_service.create_hive(db=db, hive=hive, user_id=current_user.id)
    return schemas.HiveResponse.model_validate(db_hive)


@app.get("/hives/", response_model=List[schemas.HiveResponse])
async def read_hives(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    hives = await hive_service.get_hives_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return [schemas.HiveResponse.model_validate(hive) for hive in hives]


@app.get("/hives/{hive_id}", response_model=schemas.HiveWithStats)
async def read_hive(
    hive_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    hive = await hive_service.get_hive_with_stats(db, hive_id, current_user.id)
    if hive is None:
        raise HTTPException(status_code=404, detail="Hive not found")
    return hive


@app.put("/hives/{hive_id}", response_model=schemas.HiveResponse)
async def update_hive(
    hive_id: int,
    hive: schemas.HiveUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    db_hive = await hive_service.get(db, hive_id)
    if db_hive is None:
        raise HTTPException(status_code=404, detail="Hive not found")
    if db_hive.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    updated_hive = await hive_service.update(
        db, hive_id, **hive.model_dump(exclude_unset=True)
    )
    return schemas.HiveResponse.model_validate(updated_hive)


@app.post("/inspections/", response_model=schemas.InspectionResponse)
async def create_inspection(
    inspection: schemas.InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем, что улей принадлежит пользователю
    hive = await hive_service.get(db, inspection.hive_id)
    if not hive or hive.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hive not found")
    
    db_inspection = await inspection_service.create_inspection(
        db=db, inspection=inspection, user_id=current_user.id
    )
    return {
        "id": db_inspection.id,
        "hive_id": db_inspection.hive_id,
        "temperature": db_inspection.temperature,
        "humidity": db_inspection.humidity,
        "weight": db_inspection.weight,
        "notes": db_inspection.notes,
        "user_id": db_inspection.user_id,
        "created_at": db_inspection.created_at,
        "updated_at": db_inspection.updated_at
    }


@app.get("/hives/{hive_id}/inspections/", response_model=List[schemas.InspectionResponse])
async def read_inspections(
    hive_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    # Проверяем, что улей принадлежит пользователю
    hive = await hive_service.get(db, hive_id)
    if not hive or hive.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Hive not found")
    
    inspections = await inspection_service.get_inspections_by_hive(
        db, hive_id=hive_id, user_id=current_user.id, skip=skip, limit=limit
    )
    return [
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
        for inspection in inspections
    ] 