from uuid import UUID, uuid4
from pydantic import Field, field_validator
from datetime import datetime # Ensure datetime and timezone are available
from typing import Optional
from .base import TimestampMixin # Relative import
from .enums import AppointmentStatusEnum # Relative import

class AppointmentModel(TimestampMixin):
    """
    Represents an appointment in the system.
    Internal data model.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the appointment.")
    patient_id: UUID = Field(..., description="ID of the patient for this appointment.")
    doctor_id: UUID = Field(..., description="ID of the doctor for this appointment.")
    appointment_date_time: datetime = Field(..., description="Date and time of the appointment (UTC).")
    status: AppointmentStatusEnum = Field(default=AppointmentStatusEnum.PENDING, description="Current status of the appointment.")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes for the appointment (e.g., reason for cancellation).")


    @field_validator('appointment_date_time')
    @classmethod
    def ensure_future_or_present_datetime(cls, v: datetime) -> datetime:
        """
        Validate that the appointment datetime is not in the past if the appointment is new or being scheduled.
        It's crucial that 'v' is timezone-aware if comparing with datetime.now(timezone.utc).
        Pydantic v2 generally passes timezone-aware datetimes if the input string includes timezone info
        or if it's constructed as timezone-aware.
        """
        # Ensure 'v' is timezone-aware before comparison if it might not be.
        # If 'v' is naive, it should be localized or assumed to be UTC.
        # For simplicity, we assume 'v' will be provided as or converted to UTC.
        # if v.tzinfo is None:
        #     v = v.replace(tzinfo=timezone.utc) # Or handle as an error if naive datetimes are not allowed

        # This validation is context-dependent. For creating NEW appointments, it makes sense.
        # For loading existing data, or updating status to 'Completed' for a past appointment,
        # this rule might need to be bypassed or handled in the service layer.
        # if v < datetime.now(timezone.utc) and status not in [AppointmentStatusEnum.COMPLETED, AppointmentStatusEnum.CANCELLED]:
        #    raise ValueError('Appointment date and time cannot be in the past for new or active appointments.')
        return v

    class Config:
        from_attributes = True
