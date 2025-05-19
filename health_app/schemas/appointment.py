from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class AppointmentStatus(str, Enum):
    scheduled = "Scheduled"
    completed = "Completed"
    cancelled = "Cancelled"

class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_datetime: datetime
    status: AppointmentStatus = AppointmentStatus.scheduled

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    appointment_datetime: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None

class AppointmentOut(AppointmentBase):
    id: UUID
    date_created: datetime
    date_updated: datetime
    date_deleted: Optional[datetime] = None

    class Config:
        orm_mode = True
