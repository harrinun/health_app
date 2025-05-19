from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class MedicalRecordBase(BaseModel):
    patient_id: UUID
    diagnosis: str
    prescriptions: List[str]
    treatment_date: datetime
    doctor_notes: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordUpdate(BaseModel):
    diagnosis: Optional[str] = None
    prescriptions: Optional[List[str]] = None
    treatment_date: Optional[datetime] = None
    doctor_notes: Optional[str] = None

class MedicalRecordOut(MedicalRecordBase):
    id: UUID
    date_created: datetime
    date_updated: Optional[datetime]
    date_deleted: Optional[datetime]

    class Config:
        orm_mode = True
