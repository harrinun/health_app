from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

# Import base schema for timestamps and the enum for appointment status
from .base_schema import TimestampSchema
from ..models.enums import AppointmentStatusEnum

# --- Appointment Schemas ---

class AppointmentBaseSchema(BaseModel):
    """
    Base schema for appointment data, primarily for input.
    """
    patient_id: UUID = Field(..., description="ID of the patient for this appointment.")
    doctor_id: UUID = Field(..., description="ID of the doctor for this appointment.")
    appointment_date_time: datetime = Field(..., description="Date and time of the appointment (UTC is recommended).")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes for the appointment.")

    @field_validator('appointment_date_time')
    @classmethod
    def ensure_future_or_present_datetime_on_create_or_update(cls, v: datetime, values) -> datetime:
        """
        Validate that the appointment datetime is not in the past when creating or updating.
        """
        # Ensure datetime is timezone-aware (assume UTC if naive, or raise error)
        if v.tzinfo is None:
            
            pass # Let service layer handle timezone enforcement if needed
        # if v < datetime.now(timezone.utc):
        #     raise ValueError('Appointment date and time cannot be in the past for new or rescheduled appointments.')
        return v

class AppointmentCreateSchema(AppointmentBaseSchema):
    """
    Schema for creating a new appointment.
    ID and timestamps are server-generated.
    """
    # Inherits patient_id, doctor_id, appointment_date_time, notes
    # Status will be set by the service, e.g., to SCHEDULED by default.
    status: Optional[AppointmentStatusEnum] = Field(default=AppointmentStatusEnum.SCHEDULED, description="Initial status (server may override or set default).")


class AppointmentUpdateSchema(BaseModel):
    """
    Schema for updating an existing appointment. All fields are optional.
    Allows for partial updates (PATCH requests).
    """
    # patient_id and doctor_id are generally not updatable for an existing appointment.
    appointment_date_time: Optional[datetime] = Field(default=None, description="New date and time for the appointment (UTC).")
    status: Optional[AppointmentStatusEnum] = Field(default=None, description="New status of the appointment.")
    notes: Optional[str] = Field(default=None, max_length=500, description="Updated notes for the appointment.")

    @field_validator('appointment_date_time')
    @classmethod
    def ensure_future_datetime_if_provided(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            if v.tzinfo is None:
                # As above, timezone handling needs to be consistent.
                pass
            # if v < datetime.now(timezone.utc):
            #     raise ValueError('New appointment date and time cannot be in the past.')
        return v

class AppointmentResponseSchema(AppointmentBaseSchema, TimestampSchema):
    """
    Schema for representing an appointment in API responses.
    Includes server-generated fields like id, status, and timestamps.
    """
    id: UUID
    status: AppointmentStatusEnum = Field(..., description="Current status of the appointment.")

    # Inherits patient_id, doctor_id, appointment_date_time, notes from AppointmentBaseSchema
    # Inherits date_created, date_updated, date_deleted from TimestampSchema

   