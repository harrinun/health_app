from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
from .patient import EmergencyContact
from uuid import UUID


class DoctorBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: EmailStr
    address: str
    emergency_contact: EmergencyContact
    specialty: str
    years_of_experience: int


class DoctorCreate(DoctorBase):
    pass



class DoctorUpdate(DoctorBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: date
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[EmergencyContact] = None
    specialty: Optional[str] = None
    years_of_experience: Optional[int] = None


class DoctorOut(DoctorBase):
    id: UUID
    date_created: datetime
    date_deleted: Optional[datetime] = None

    class Config:
        orm_mode = True