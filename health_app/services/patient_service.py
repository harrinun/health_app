from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID


from ..models.patient_model import PatientModel
from ..models.base import Biodata, ContactInformation, EmergencyContact
from ..models.enums import GenderEnum
from ..repository.patient_repository import PatientRepository
from ..utils.exceptions import ( # Import custom exceptions
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
    """
    def __init__(self, patient_repository: PatientRepository):
        self.patient_repository = patient_repository

    def _get_last_folder_code_parts(self) -> Tuple[str, int]:
        all_patients = self.patient_repository.get_all(include_deleted=True, limit=None)
        if not all_patients:
            return "AAA", 0

        last_alpha = "AAA"
        last_numeric = 0
        
        sorted_patients = sorted(
            all_patients,
            key=lambda p: p.patient_folder_number if hasattr(p, 'patient_folder_number') and p.patient_folder_number else "GHA-TM-AAA0000", # Default for sorting if None/empty
            reverse=True
        )

        if sorted_patients and hasattr(sorted_patients[0], 'patient_folder_number') and sorted_patients[0].patient_folder_number:
            latest_folder_number = sorted_patients[0].patient_folder_number
            try:
                prefix_and_code = latest_folder_number.split("GHA-TM-")
                if len(prefix_and_code) == 2 and len(prefix_and_code[1]) == 7:
                    code_part = prefix_and_code[1] # "AAB0012"
                    last_alpha = code_part[:3] # "AAB"
                    last_numeric = int(code_part[3:]) # 12
                else:
                    logger.warning(f"Could not parse latest folder number format: {latest_folder_number}. Defaulting.")
            except (ValueError, IndexError) as e: # More specific exception catching
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
            logger.error(f"Concurrency issue: Generated folder number {new_folder_number} already exists. This should be rare.")
            # For now, we raise an exception suggesting a concurrency problem.
            raise ConcurrencyException(f"Generated patient folder number {new_folder_number} already exists. Please try again.")

        return new_folder_number

    def create_patient(
        self, 
        first_name: str, 
        last_name: str, 
        date_of_birth: datetime.date,
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
            logger.error(f"Invalid gender string provided: {gender_str}")
            raise InvalidOperationException(f"Invalid gender: '{gender_str}'. Valid options are: {[ge.value for ge in GenderEnum]}")

        folder_number = self._generate_next_patient_folder_number()

        biodata = Biodata(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth, # Validator is in Biodata model
            gender=gender_enum
        )
        contact_information = ContactInformation(
            phone_number=phone_number,
            email=email, 
            address=address
        )
        emergency_contact = EmergencyContact(
            full_name=emergency_full_name,
            relationship=emergency_relationship,
            phone_number=emergency_phone_number
        )

        new_patient = PatientModel(
            patient_folder_number=folder_number,
            biodata=biodata,
            contact_information=contact_information,
            emergency_contact=emergency_contact
        )
        
        try:
            created_patient = self.patient_repository.add(new_patient)
            logger.info(f"Patient created successfully with folder number: {folder_number} and ID: {created_patient.id}")
            return created_patient
        except ValueError as e: # Catch specific ValueError from repository.add (e.g. ID exists)
            logger.error(f"Error adding patient to repository: {e}")
            # This might indicate a pre-existing ID, which should be rare with UUIDs
            # Or if the add method raises ValueError for other reasons.
            raise InvalidOperationException(f"Could not create patient: {e}")


    def get_patient_by_id(self, patient_id: UUID, include_deleted: bool = False) -> Optional[PatientModel]:
        logger.debug(f"Fetching patient by ID: {patient_id}, include_deleted: {include_deleted}")
        patient = self.patient_repository.get_by_id(patient_id, include_deleted=include_deleted)
        if not patient:
            logger.debug(f"Patient with ID {patient_id} not found or does not meet deletion criteria.")
        return patient

    def get_all_patients(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[PatientModel]:
        logger.debug(f"Fetching all patients. Skip: {skip}, Limit: {limit}, Include Deleted: {include_deleted}")
        return self.patient_repository.get_all(skip=skip, limit=limit, include_deleted=include_deleted)

    def update_patient(self, patient_id: UUID, update_fields: dict) -> Optional[PatientModel]:
        # Check if the patient exists and is active (update shouldn't apply to soft-deleted)
        patient_to_update = self.patient_repository.get_by_id(patient_id, include_deleted=False)
        if not patient_to_update:
            logger.warning(f"Update failed: Active patient with ID {patient_id} not found.")
            return None 

        logger.info(f"Attempting to update patient ID: {patient_id} with data: {update_fields}")
        updated_patient = self.patient_repository.update(patient_id, update_fields)
        if not updated_patient:
            # This could be due to internal repository logic or if update returns None on no change.
            logger.warning(f"Patient with ID {patient_id} was not updated by repository.")
        return updated_patient


    def soft_delete_patient(self, patient_id: UUID) -> Optional[PatientModel]:
        patient = self.patient_repository.get_by_id(patient_id, include_deleted=True) # Check if exists at all
        if not patient:
            raise ResourceNotFoundException(resource_name="Patient", resource_id=patient_id)
        
        if patient.date_deleted is not None:
            logger.info(f"Patient {patient_id} is already soft-deleted.")
            return patient # Or raise InvalidOperationException("Patient already deleted")

        logger.info(f"Attempting to soft delete patient ID: {patient_id}")
        deleted_patient = self.patient_repository.soft_delete(patient_id)
        if not deleted_patient: 
             logger.error(f"Soft delete failed unexpectedly for patient {patient_id} after existence check.")
             raise InvalidOperationException(f"Could not soft delete patient {patient_id}.")
        return deleted_patient


    def restore_patient(self, patient_id: UUID) -> Optional[PatientModel]:
        patient = self.patient_repository.get_by_id(patient_id, include_deleted=True)
        if not patient:
            raise ResourceNotFoundException(resource_name="Patient", resource_id=patient_id)

        if patient.date_deleted is None:
            logger.info(f"Patient {patient_id} is not soft-deleted. No restore action needed.")
            # Depending on desired API behavior, could return patient or raise error.
            raise InvalidOperationException(f"Patient with ID {patient_id} is not deleted, cannot restore.")

        logger.info(f"Attempting to restore patient ID: {patient_id}")
        restored_patient = self.patient_repository.restore(patient_id)
        if not restored_patient: # Should not happen if found and was deleted, unless race condition
            logger.error(f"Restore failed unexpectedly for patient {patient_id} after checks.")
            raise InvalidOperationException(f"Could not restore patient {patient_id}.")
        return restored_patient
    
    def get_patient_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        logger.debug(f"Fetching patient by folder number: {folder_number}")
        patient = self.patient_repository.find_by_folder_number(folder_number)
        # No ResourceNotFoundException here for consistency with get_by_id if None is acceptable return.
        return patient

