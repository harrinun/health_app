from datetime import date
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from ..models.patient_model import PatientModel
from ..models.base import Biodata, ContactInformation, EmergencyContact
from ..models.enums import GenderEnum
# Change this import to the interface
from ..repository.patient_interface import IPatientRepository
from ..utils.exceptions import (
    ResourceNotFoundException,
    InvalidOperationException,
    ConcurrencyException
)
import logging

logger = logging.getLogger(__name__)

class PatientService:
    """
    Service layer for managing patients.
    Contains business logic related to patient operations.
    It is completely decoupled from the data storage mechanism.
    """
    # Change the type hint to the abstract interface
    def __init__(self, patient_repository: IPatientRepository):
        self.patient_repository = patient_repository

    def _get_last_folder_code_parts(self) -> Tuple[str, int]:
        # This method now explicitly calls the repository method for this purpose
        all_patients = self.patient_repository.get_all_for_folder_number_generation()
        if not all_patients:
            return "AAA", 0

        last_alpha = "AAA"
        last_numeric = 0
        
        sorted_patients = sorted(
            all_patients,
            key=lambda p: p.patient_folder_number if p.patient_folder_number else "GHA-TM-AAA0000",
            reverse=True
        )

        if sorted_patients and sorted_patients[0].patient_folder_number:
            latest_folder_number = sorted_patients[0].patient_folder_number
            try:
                prefix_and_code = latest_folder_number.split("GHA-TM-")
                if len(prefix_and_code) == 2 and len(prefix_and_code[1]) == 7:
                    code_part = prefix_and_code[1]
                    last_alpha = code_part[:3]
                    last_numeric = int(code_part[3:])
                else:
                    logger.warning(f"Could not parse latest folder number format: {latest_folder_number}. Defaulting.")
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing folder number parts from '{latest_folder_number}': {e}. Defaulting.")
            except Exception as e:
                logger.error(f"Unexpected error parsing folder number {latest_folder_number}: {e}. Defaulting.")
        
        return last_alpha, last_numeric


    def _generate_next_patient_folder_number(self) -> str:
        current_alpha, current_numeric = self._get_last_folder_code_parts()

        next_numeric = current_numeric + 1
        next_alpha_str = current_alpha

        if next_numeric > 9999:
            next_numeric = 1
            alpha_chars = list(next_alpha_str)
            for i in range(2, -1, -1):
                if alpha_chars[i] == 'Z':
                    alpha_chars[i] = 'A'
                    if i == 0:
                        logger.critical("Patient folder number range exhausted (all ZZZ9999 used).")
                        raise InvalidOperationException("Patient folder number range exhausted.")
                else:
                    alpha_chars[i] = chr(ord(alpha_chars[i]) + 1)
                    break
            next_alpha_str = "".join(alpha_chars)
        
        new_folder_number = f"GHA-TM-{next_alpha_str}{next_numeric:04d}"

        if self.patient_repository.find_by_folder_number(new_folder_number):
            logger.error(f"Concurrency issue: Generated folder number {new_folder_number} already exists.")
            raise ConcurrencyException(f"Generated patient folder number {new_folder_number} already exists. Please try again.")

        return new_folder_number

    def create_patient(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        gender_str: str,
        phone_number: str,
        address: str,
        emergency_full_name: str,
        emergency_relationship: str,
        emergency_phone_number: str,
        email: Optional[str] = None
    ) -> PatientModel:
        try:
            gender_enum = GenderEnum(gender_str)
        except ValueError:
            raise InvalidOperationException(f"Invalid gender: '{gender_str}'. Valid options are: {[ge.value for ge in GenderEnum]}")

        folder_number = self._generate_next_patient_folder_number()

        new_patient = PatientModel(
            patient_folder_number=folder_number,
            biodata=Biodata(
                first_name=first_name, last_name=last_name, date_of_birth=date_of_birth, gender=gender_enum
            ),
            contact_information=ContactInformation(
                phone_number=phone_number, email=email, address=address
            ),
            emergency_contact=EmergencyContact(
                full_name=emergency_full_name, relationship=emergency_relationship, phone_number=emergency_phone_number
            )
        )
        
        try:
            created_patient = self.patient_repository.add(new_patient)
            logger.info(f"Patient created successfully with folder number: {folder_number} and ID: {created_patient.id}")
            return created_patient
        except ValueError as e:
            logger.error(f"Error adding patient to repository: {e}")
            raise InvalidOperationException(f"Could not create patient: {e}")


    def get_patient_by_id(self, patient_id: UUID, include_deleted: bool = False) -> Optional[PatientModel]:
        return self.patient_repository.get_by_id(patient_id, include_deleted=include_deleted)

    def get_all_patients(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[PatientModel]:
        return self.patient_repository.get_all(skip=skip, limit=limit, include_deleted=include_deleted)

    def update_patient(self, patient_id: UUID, update_fields: Dict[str, Any]) -> Optional[PatientModel]:
        # The repository's update method should handle checking for existence.
        # This service layer method simply passes the data along.
        updated_patient = self.patient_repository.update(patient_id, update_fields)
        if not updated_patient:
            raise ResourceNotFoundException(resource_name="Active Patient", resource_id=patient_id)
        return updated_patient

    def soft_delete_patient(self, patient_id: UUID):
        deleted_patient = self.patient_repository.soft_delete(patient_id)
        if not deleted_patient:
            raise ResourceNotFoundException(resource_name="Active Patient", resource_id=patient_id)
        return deleted_patient

    def restore_patient(self, patient_id: UUID):
        restored_patient = self.patient_repository.restore(patient_id)
        if not restored_patient:
            raise ResourceNotFoundException(resource_name="Soft-deleted Patient", resource_id=patient_id)
        return restored_patient

    def get_patient_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        return self.patient_repository.find_by_folder_number(folder_number)

