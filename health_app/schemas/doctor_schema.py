from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime # For timestamp fields in response

# Import base schemas and timestamp schema from health_app/schemas/base_schema.py
from .base_schema import (
    BiodataBaseSchema, 
    ContactInformationBaseSchema, 
    EmergencyContactBaseSchema, 
    TimestampSchema
)

# --- Doctor Schemas ---

class DoctorBaseSchema(BaseModel):
    """
    Base schema for doctor data, containing all required fields.
    """
    biodata: BiodataBaseSchema
    specialty: str = Field(..., min_length=2, max_length=100, description="Doctor's medical specialty (e.g., Cardiology).")
    years_of_experience: int = Field(..., ge=0, le=70, description="Number of years the doctor has been practicing.")
    contact_information: ContactInformationBaseSchema
    emergency_contact: Optional[EmergencyContactBaseSchema] = Field(default=None, description="Doctor's emergency contact details (optional).")

class DoctorCreateSchema(DoctorBaseSchema):
    """
    Schema for creating a new doctor.
    ID and timestamps are server-generated and not included here.
    """
    # All fields are inherited from DoctorBaseSchema.
    pass

class DoctorUpdateSchema(BaseModel):
    """
    Schema for updating an existing doctor. All fields are optional.
    This allows for partial updates (PATCH requests).
    """
    biodata: Optional[BiodataBaseSchema] = None
    specialty: Optional[str] = Field(default=None, min_length=2, max_length=100, description="Doctor's medical specialty.")
    years_of_experience: int = Field(..., ge=0, le=70, description="Number of years the doctor has been practicing.")
    contact_information: Optional[ContactInformationBaseSchema] = None
    emergency_contact: Optional[EmergencyContactBaseSchema] = Field(default=None, description="Doctor's emergency contact details. Set to null or omit if no change.")
    

class DoctorResponseSchema(DoctorBaseSchema, TimestampSchema):
    """
    Schema for representing a doctor in API responses.
    Includes server-generated fields like id and timestamps.
    """
    id: UUID

    # Inherits biodata, specialty, years_of_experience, contact_information, 
    # emergency_contact from DoctorBaseSchema.
    # Inherits date_created, date_updated, date_deleted from TimestampSchema.

    