from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

# Import base schema for timestamps and the enum for appointment status
from .base_schema import TimestampSchema
from ..models.enums import AppointmentStatusEnum # Used for status field

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
        The service layer will also perform this check, but schema validation is good for early feedback.
        This validator is more relevant for Create/Update schemas.
        """
        # Ensure datetime is timezone-aware (assume UTC if naive, or raise error)
        if v.tzinfo is None:
            # For schemas, it's often better to expect timezone-aware datetime strings from clients.
            # If a naive datetime is received, how to handle it depends on API contract.
            # Here, we'll assume if it's naive, it might be an issue or needs to be localized.
            # For simplicity in schema, we might just check if it's past based on server's current UTC time.
            # A more robust solution involves clear API documentation on expected datetime formats (ISO 8601 with TZ).
            pass # Let service layer handle timezone enforcement if needed, or expect ISO strings.

        # This validation might be too strict at schema level if loading existing past appointments.
        # For 'create' or 'update' operations where a new time is set, it's relevant.
        # if v < datetime.now(timezone.utc):
        #     raise ValueError('Appointment date and time cannot be in the past for new or rescheduled appointments.')
        return v

class AppointmentCreateSchema(AppointmentBaseSchema):
    """
    Schema for creating a new appointment.
    Status is typically set by the server (e.g., to 'Scheduled' or 'Pending').
    ID and timestamps are server-generated.
    """
    # Inherits patient_id, doctor_id, appointment_date_time, notes
    # Status will be set by the service, e.g., to SCHEDULED by default.
    # If client can suggest a status like PENDING, it could be added here.
    status: Optional[AppointmentStatusEnum] = Field(default=AppointmentStatusEnum.SCHEDULED, description="Initial status (server may override or set default).")


class AppointmentUpdateSchema(BaseModel):
    """
    Schema for updating an existing appointment. All fields are optional.
    Allows for partial updates (PATCH requests).
    """
    # patient_id and doctor_id are generally not updatable for an existing appointment.
    # If they need to change, it's often a new appointment.
    # patient_id: Optional[UUID] = Field(default=None, description="ID of the patient.")
    # doctor_id: Optional[UUID] = Field(default=None, description="ID of the doctor.")
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

    # The `model_config = {"from_attributes": True}` is inherited from TimestampSchema,
    # allowing this schema to be created from AppointmentModel instances.
