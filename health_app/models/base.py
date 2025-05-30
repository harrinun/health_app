from datetime import datetime, date, timezone 
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from .enums import GenderEnum 

class TimestampMixin(BaseModel):
    """
    A mixin model that adds timestamp fields for tracking record creation,
    updates, and soft deletion.
    `default_factory` is used to generate default values at the time of model instantiation.
    Uses timezone-aware UTC datetimes.
    """
    date_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the record was created (UTC).")
    date_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the record was last updated (UTC).")
    date_deleted: Optional[datetime] = Field(default=None, description="Timestamp of when the record was soft-deleted (UTC). Null if not deleted.")

 
class Biodata(BaseModel):
    """
    Stores personal identification details.
    """
    first_name: str = Field(..., min_length=1, max_length=100, description="Person's first name.")
    last_name: str = Field(..., min_length=1, max_length=100, description="Person's last name.")
    date_of_birth: date = Field(..., description="Person's date of birth.")
    gender: GenderEnum = Field(..., description="Person's gender.")

    @field_validator('date_of_birth')
    @classmethod
    def ensure_not_future_date(cls, v: date) -> date:
        """Validate that the date of birth is today or in the past."""
        if v > date.today(): 
            raise ValueError('Date of birth must be today or in the past.')
        return v


class ContactInformation(BaseModel):
    """
    Stores contact information.
    """
    phone_number: str = Field(..., pattern=r"^\+?[0-9\s-]{7,20}$", description="Primary phone number (e.g., +123-456-7890).")
    email: Optional[EmailStr] = Field(default=None, description="Email address (optional). Pydantic's EmailStr validates email format.")
    address: str = Field(..., min_length=5, max_length=255, description="Physical address.")


class EmergencyContact(BaseModel):
    """
    Stores details for an emergency contact.
    """
    full_name: str = Field(..., min_length=1, max_length=200, description="Full name of the emergency contact.")
    relationship: str = Field(..., min_length=2, max_length=50, description="Relationship to the person (e.g., Spouse, Parent).")
    phone_number: str = Field(..., pattern=r"^\+?[0-9\s-]{7,20}$", description="Emergency contact's phone number.")
