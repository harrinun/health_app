from uuid import UUID, uuid4
from pydantic import Field
from datetime import date
from typing import Optional, List
from .base import TimestampMixin # Relative import

class MedicalRecordModel(TimestampMixin):
    """
    Represents a medical record for a patient.
    Internal data model.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the medical record.")
    patient_id: UUID = Field(..., description="ID of the patient this medical record belongs to.")
    appointment_id: Optional[UUID] = Field(default=None, description="ID of the appointment related to this record (optional).")
    diagnosis: str = Field(..., min_length=3, description="Diagnosis made by the doctor.")
    prescriptions: List[str] = Field(default_factory=list, description="List of prescribed medications or treatments.")
    treatment_date: date = Field(default_factory=date.today, description="Date the treatment or consultation occurred.") # date.today() is fine
    doctor_notes: Optional[str] = Field(default=None, max_length=2000, description="Additional notes from the doctor (optional).")
    attending_doctor_id: Optional[UUID] = Field(default=None, description="ID of the doctor who created/updated this record (optional).")


    class Config:
        from_attributes = True

