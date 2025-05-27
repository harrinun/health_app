from uuid import UUID, uuid4
from pydantic import Field

from .base import TimestampMixin, Biodata, ContactInformation, EmergencyContact 

class PatientModel(TimestampMixin): # Inherits date_created, date_updated, date_deleted
    """
    Represents a patient in the system.
    This is the internal data model, often used by repositories.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the patient.")
    patient_folder_number: str = Field(
        ..., 
        description="Clinic-specific unique folder number for the patient (e.g., GHA-TM-AAA0001).",
        examples=["GHA-TM-AAA0001"]
    )
    biodata: Biodata = Field(..., description="Patient's personal and demographic information.")
    contact_information: ContactInformation = Field(..., description="Patient's contact details.")
    emergency_contact: EmergencyContact = Field(..., description="Patient's emergency contact details.")


    model_config = {
        "from_attributes": True,  # Enables creating model instances from ORM objects or other attribute-based sources.
        "json_schema_extra": {    # Example of adding extra info to the JSON schema
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "patient_folder_number": "GHA-TM-ABC1234",
                "biodata": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1990-01-15",
                    "gender": "Male"
                },
                "contact_information": {
                    "phone_number": "+1234567890",
                    "email": "john.doe@example.com",
                    "address": "123 Main St, Anytown, USA"
                },
                "emergency_contact": {
                    "full_name": "Jane Doe",
                    "relationship": "Spouse",
                    "phone_number": "+1987654321"
                },
                "date_created": "2023-01-01T10:00:00Z",
                "date_updated": "2023-01-01T10:00:00Z",
                "date_deleted": None
            }
        }
    }

