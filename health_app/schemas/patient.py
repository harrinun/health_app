from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, date
from .emergency_contact import EmergencyContact
from uuid import UUID


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    contact_info: str
    address: str
    emergency_contact: EmergencyContact


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: date
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[EmergencyContact] = None


class PatientOut(PatientBase):
    id: UUID
    date_created: datetime
    date_deleted: Optional[datetime] = None

    class Config:
        orm_mode = True


class PatientResponse(PatientBase):
    id: str
    date_created: datetime
    date_updated: Optional[datetime]
    date_deleted: Optional[datetime]
