from uuid import UUID, uuid4
from pydantic import Field
from typing import Optional

from .base import TimestampMixin, Biodata, ContactInformation, EmergencyContact 



class DoctorModel(TimestampMixin):
    """
    Represents a doctor in the system.
    Internal data model.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the doctor.")
    biodata: Biodata = Field(..., description="Doctor's personal and demographic information.")
    specialty: str = Field(..., min_length=2, max_length=100, description="Doctor's medical specialty (e.g., Cardiology).")
    years_of_experience: int = Field(..., ge=0, le=70, description="Number of years the doctor has been practicing (non-negative).")
    contact_information: ContactInformation = Field(..., description="Doctor's contact details.")
    emergency_contact: Optional[EmergencyContact] = Field(default=None, description="Doctor's emergency contact details (optional).")

    class Config:
        from_attributes = True  # This allows the Pydantic model to be created from arbitrary objects that have attributes