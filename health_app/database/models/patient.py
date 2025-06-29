"""
SQLAlchemy Patient model for database operations.
This model represents the patients table in PostgreSQL and works alongside
the Pydantic PatientModel for data validation and serialization.
"""

from sqlalchemy import Column, String, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..config import Base
from .base import TimestampMixin, BiodataColumns, ContactInformationColumns, EmergencyContactColumns


class PatientDB(Base, TimestampMixin, BiodataColumns, ContactInformationColumns, EmergencyContactColumns):
    """
    SQLAlchemy model for Patient table.
    
    This model inherits from multiple mixins to compose the full patient schema:
    - TimestampMixin: Provides date_created, date_updated, date_deleted
    - BiodataColumns: Provides first_name, last_name, date_of_birth, gender
    - ContactInformationColumns: Provides phone_number, email, address
    - EmergencyContactColumns: Provides emergency contact fields
    """
    
    __tablename__ = "patients"
    
    # Primary key - UUID
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique identifier for the patient"
    )
    
    # Unique patient folder number
    patient_folder_number = Column(
        String(50), 
        nullable=False, 
        unique=True,
        comment="Unique folder number for the patient (e.g., GHA-TM-AAA0001)"
    )
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_patient_folder_number', 'patient_folder_number'),
        Index('idx_patient_last_name', 'last_name'),
        Index('idx_patient_email', 'email'),
        Index('idx_patient_deleted', 'date_deleted'),
        Index('idx_patient_created', 'date_created'),
    )
    
    def __repr__(self) -> str:
        """String representation of the Patient model"""
        return f"<PatientDB(id={self.id}, folder_number={self.patient_folder_number}, name={self.first_name} {self.last_name})>"
    
    def is_deleted(self) -> bool:
        """Check if the patient is soft-deleted"""
        return self.date_deleted is not None
    
    def get_full_name(self) -> str:
        """Get the patient's full name"""
        return f"{self.first_name} {self.last_name}"