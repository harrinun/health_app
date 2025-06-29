"""
SQLAlchemy-based implementation of the Patient Repository Interface.

This class handles all database operations for the Patient model using SQLAlchemy's ORM.
It translates between the Pydantic `PatientModel` used by the service layer and the
SQLAlchemy `PatientDB` model used for database interaction.
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .patient_interface import IPatientRepository
from ..models.patient_model import PatientModel, Biodata, ContactInformation, EmergencyContact
from ..database.models.patient import PatientDB

logger = logging.getLogger(__name__)

class PatientSqlRepository(IPatientRepository):
    """
    Patient Repository implementation for SQLAlchemy.
    """
    def __init__(self, db_session: Session):
        self._db = db_session

    def _db_to_pydantic(self, db_patient: PatientDB) -> PatientModel:
        """Converts a PatientDB SQLAlchemy object to a PatientModel Pydantic object."""
        return PatientModel(
            id=db_patient.id,
            patient_folder_number=db_patient.patient_folder_number,
            biodata=Biodata(
                first_name=db_patient.first_name,
                last_name=db_patient.last_name,
                date_of_birth=db_patient.date_of_birth,
                gender=db_patient.gender
            ),
            contact_information=ContactInformation(
                phone_number=db_patient.phone_number,
                email=db_patient.email,
                address=db_patient.address
            ),
            emergency_contact=EmergencyContact(
                full_name=db_patient.emergency_full_name,
                relationship=db_patient.emergency_relationship,
                phone_number=db_patient.emergency_phone_number
            ),
            date_created=db_patient.date_created,
            date_updated=db_patient.date_updated,
            date_deleted=db_patient.date_deleted
        )

    def get_all(self, skip: int = 0, limit: Optional[int] = 100, include_deleted: bool = False) -> List[PatientModel]:
        query = self._db.query(PatientDB)
        if not include_deleted:
            query = query.filter(PatientDB.date_deleted.is_(None))
        
        db_patients = query.offset(skip).limit(limit).all()
        return [self._db_to_pydantic(p) for p in db_patients]

    def get_by_id(self, item_id: UUID, include_deleted: bool = False) -> Optional[PatientModel]:
        query = self._db.query(PatientDB).filter(PatientDB.id == item_id)
        if not include_deleted:
            query = query.filter(PatientDB.date_deleted.is_(None))
        
        db_patient = query.first()
        return self._db_to_pydantic(db_patient) if db_patient else None

    def add(self, item_to_add: PatientModel) -> PatientModel:
        db_patient = PatientDB(
            id=item_to_add.id,
            patient_folder_number=item_to_add.patient_folder_number,
            first_name=item_to_add.biodata.first_name,
            last_name=item_to_add.biodata.last_name,
            date_of_birth=item_to_add.biodata.date_of_birth,
            gender=item_to_add.biodata.gender.value,
            phone_number=item_to_add.contact_information.phone_number,
            email=item_to_add.contact_information.email,
            address=item_to_add.contact_information.address,
            emergency_full_name=item_to_add.emergency_contact.full_name,
            emergency_relationship=item_to_add.emergency_contact.relationship,
            emergency_phone_number=item_to_add.emergency_contact.phone_number,
            date_created=item_to_add.date_created,
            date_updated=item_to_add.date_updated
        )
        self._db.add(db_patient)
        self._db.commit()
        self._db.refresh(db_patient)
        return self._db_to_pydantic(db_patient)

    def update(self, item_id: UUID, update_data: Dict[str, Any]) -> Optional[PatientModel]:
        db_patient = self._db.query(PatientDB).filter(PatientDB.id == item_id, PatientDB.date_deleted.is_(None)).first()
        if not db_patient:
            return None

        # Flatten nested Pydantic models into the flat update_data
        if 'biodata' in update_data:
            for key, value in update_data['biodata'].items():
                setattr(db_patient, key, value)
            del update_data['biodata']
        
        if 'contact_information' in update_data:
            for key, value in update_data['contact_information'].items():
                setattr(db_patient, key, value)
            del update_data['contact_information']

        if 'emergency_contact' in update_data:
            if 'full_name' in update_data['emergency_contact']:
                db_patient.emergency_full_name = update_data['emergency_contact']['full_name']
            if 'relationship' in update_data['emergency_contact']:
                db_patient.emergency_relationship = update_data['emergency_contact']['relationship']
            if 'phone_number' in update_data['emergency_contact']:
                db_patient.emergency_phone_number = update_data['emergency_contact']['phone_number']
            del update_data['emergency_contact']

        # Update remaining top-level fields
        for key, value in update_data.items():
            setattr(db_patient, key, value)

        db_patient.date_updated = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(db_patient)
        return self._db_to_pydantic(db_patient)

    def soft_delete(self, item_id: UUID) -> Optional[PatientModel]:
        db_patient = self._db.query(PatientDB).filter(PatientDB.id == item_id, PatientDB.date_deleted.is_(None)).first()
        if not db_patient:
            return None
        
        db_patient.date_deleted = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(db_patient)
        return self._db_to_pydantic(db_patient)

    def restore(self, item_id: UUID) -> Optional[PatientModel]:
        db_patient = self._db.query(PatientDB).filter(PatientDB.id == item_id, PatientDB.date_deleted.is_not(None)).first()
        if not db_patient:
            return None
        
        db_patient.date_deleted = None
        self._db.commit()
        self._db.refresh(db_patient)
        return self._db_to_pydantic(db_patient)

    def find_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        db_patient = self._db.query(PatientDB).filter(
            PatientDB.patient_folder_number == folder_number, 
            PatientDB.date_deleted.is_(None)
        ).first()
        return self._db_to_pydantic(db_patient) if db_patient else None

    def find_by_last_name(self, last_name: str) -> List[PatientModel]:
        db_patients = self._db.query(PatientDB).filter(
            PatientDB.last_name.ilike(f"%{last_name}%"), 
            PatientDB.date_deleted.is_(None)
        ).all()
        return [self._db_to_pydantic(p) for p in db_patients]
        
    def get_all_for_folder_number_generation(self) -> List[PatientModel]:
        all_db_patients = self._db.query(PatientDB).all()
        return [self._db_to_pydantic(p) for p in all_db_patients]
