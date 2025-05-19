from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from health_app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentOut,
    AppointmentStatus,
)
from health_app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])
service = AppointmentService()

@router.get("/", response_model=List[AppointmentOut])
def list_appointments(
    status: Optional[AppointmentStatus] = Query(None),
    date: Optional[datetime] = Query(None),
):
    try:
        return service.list_appointments(status=status, date=date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: UUID):
    appointment = service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return appointment

@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate):
    try:
        return service.create_appointment(appointment)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: UUID, updates: AppointmentUpdate):
    try:
        updated = service.update_appointment(appointment_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Appointment not found.")
        return updated
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: UUID):
    deleted = service.delete_appointment(appointment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Appointment not found or already deleted.")
