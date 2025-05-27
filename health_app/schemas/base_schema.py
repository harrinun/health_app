from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID

# Import enums from the models directory. Schemas can use the same enums
# as they define valid value sets.
from ..models.enums import GenderEnum

class BiodataBaseSchema(BaseModel):
    """
    Base schema for biographical data.
    Used for request data (creation/update).
    """
    first_name: str = Field(..., min_length=1, max_length=100, description="Person's first name.")
    last_name: str = Field(..., min_length=1, max_length=100, description="Person's last name.")
    date_of_birth: date = Field(..., description="Person's date of birth.")
    gender: GenderEnum = Field(..., description="Person's gender.")

    @field_validator('date_of_birth')
    @classmethod
    def ensure_past_date(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError('Date of birth must be in the past.')
        return v

class ContactInformationBaseSchema(BaseModel):
    """
    Base schema for contact information.
    Used for request data.
    """
    phone_number: str = Field(..., pattern=r"^\+?[0-9\s-]{7,20}$", description="Primary phone number.")
    email: Optional[EmailStr] = Field(default=None, description="Email address (optional).")
    address: str = Field(..., min_length=5, max_length=255, description="Physical address.")

class EmergencyContactBaseSchema(BaseModel):
    """
    Base schema for emergency contact details.
    Used for request data.
    """
    full_name: str = Field(..., min_length=1, max_length=200, description="Full name of the emergency contact.")
    relationship: str = Field(..., min_length=2, max_length=50, description="Relationship to the person.")
    phone_number: str = Field(..., pattern=r"^\+?[0-9\s-]{7,20}$", description="Emergency contact's phone number.")

# For response schemas that include timestamps (these mirror TimestampMixin from models)
class TimestampSchema(BaseModel):
    date_created: datetime
    date_updated: datetime
    date_deleted: Optional[datetime] = None

    # Pydantic v2 config for ORM mode (from_attributes)
    model_config = {
        "from_attributes": True 
    }