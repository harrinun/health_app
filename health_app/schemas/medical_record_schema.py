from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date

# Import base schema for timestamps
from .base_schema import TimestampSchema

# --- Medical Record Schemas ---

class MedicalRecordBaseSchema(BaseModel):
    """
    Base schema for medical record data, primarily for input.
    """
    patient_id: UUID = Field(..., description="ID of the patient this medical record belongs to.")
    diagnosis: str = Field(..., min_length=3, description="Diagnosis made by the doctor.")
    prescriptions: List[str] = Field(default_factory=list, description="List of prescribed medications or treatments.")
    treatment_date: date = Field(..., description="Date the treatment or consultation occurred.")
    doctor_notes: Optional[str] = Field(default=None, max_length=2000, description="Additional notes from the doctor (optional).")
    attending_doctor_id: Optional[UUID] = Field(default=None, description="ID of the doctor who created/updated this record (optional).")
    appointment_id: Optional[UUID] = Field(default=None, description="ID of the appointment related to this record (optional).")

class MedicalRecordCreateSchema(MedicalRecordBaseSchema):
    """
    Schema for creating a new medical record.
    ID and timestamps are server-generated.
    """
    # All fields are inherited from MedicalRecordBaseSchema.
    pass

class MedicalRecordUpdateSchema(BaseModel):
    """
    Schema for updating an existing medical record. All fields are optional.
    'patient_id' is generally not updatable for an existing record.
    """
    # patient_id: Optional[UUID] = Field(default=None, description="Patient ID (usually not updatable).")
    diagnosis: Optional[str] = Field(default=None, min_length=3, description="Updated diagnosis.")
    prescriptions: Optional[List[str]] = Field(default=None, description="Updated list of prescriptions.")
    treatment_date: Optional[date] = Field(default=None, description="Updated treatment date.")
    doctor_notes: Optional[str] = Field(default=None, max_length=2000, description="Updated doctor notes.")
    attending_doctor_id: Optional[UUID] = Field(default=None, description="Updated ID of the attending doctor.")
    appointment_id: Optional[UUID] = Field(default=None, description="Updated ID of the related appointment.")


class MedicalRecordResponseSchema(MedicalRecordBaseSchema, TimestampSchema):
    """
    Schema for representing a medical record in API responses.
    Includes server-generated fields like id and timestamps.
    """
    id: UUID

    # Inherits fields from MedicalRecordBaseSchema and TimestampSchema.
    # The `model_config = {"from_attributes": True}` is inherited from TimestampSchema,
    # allowing this schema to be created from MedicalRecordModel instances.
