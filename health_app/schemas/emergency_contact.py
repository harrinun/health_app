from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class EmergencyContact(BaseModel):
    first_name: str
    last_name: str
    relationship: str
    phone: str
    email: EmailStr
