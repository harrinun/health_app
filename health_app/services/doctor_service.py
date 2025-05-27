from typing import List, Optional
from uuid import UUID, uuid4 
from datetime import datetime # For date_of_birth type hinting

from ..models.doctor_model import DoctorModel
from ..models.base import Biodata, ContactInformation, EmergencyContact 
from ..models.enums import GenderEnum 
from ..repository.doctor_repository import DoctorRepository
from ..utils.exceptions import ( # Import custom exceptions
    ResourceNotFoundException,
    InvalidOperationException
)
import logging

logger = logging.getLogger(__name__)

class DoctorService:
    """
    Service layer for managing doctors.
    Contains business logic related to doctor operations.
    """
    def __init__(self, doctor_repository: DoctorRepository):
        """
        Initializes the DoctorService with a DoctorRepository instance.

        Args:
            doctor_repository (DoctorRepository): An instance of the doctor repository
                                                  for data access.
        """
        self.doctor_repository = doctor_repository

    def create_doctor(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: datetime.date, 
        gender_str: str,
        specialty: str,
        years_of_experience: int,
        phone_number: str,
        address: str,
        email: Optional[str] = None,
        emergency_full_name: Optional[str] = None, 
        emergency_relationship: Optional[str] = None,
        emergency_phone_number: Optional[str] = None
    ) -> DoctorModel:
        """
        Creates a new doctor with the provided details.
        """
        try:
            gender_enum = GenderEnum(gender_str)
        except ValueError:
            logger.error(f"Invalid gender string provided for doctor: {gender_str}")
            raise InvalidOperationException(f"Invalid gender: '{gender_str}'. Valid options are: {[ge.value for ge in GenderEnum]}")

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
        
        optional_emergency_contact: Optional[EmergencyContact] = None
        if emergency_full_name and emergency_relationship and emergency_phone_number:
            optional_emergency_contact = EmergencyContact(
                full_name=emergency_full_name,
                relationship=emergency_relationship,
                phone_number=emergency_phone_number
            )
        elif any([emergency_full_name, emergency_relationship, emergency_phone_number]):
            # If some emergency contact fields are provided but not all, it's an invalid partial state
            raise InvalidOperationException("All fields (full_name, relationship, phone_number) are required for an emergency contact if any is provided.")


        new_doctor = DoctorModel(
            biodata=biodata,
            specialty=specialty,
            years_of_experience=years_of_experience, # Pydantic's conint/Field validator handles constraints
            contact_information=contact_information,
            emergency_contact=optional_emergency_contact
        )
        
        try:
            created_doctor = self.doctor_repository.add(new_doctor)
            logger.info(f"Doctor created successfully: {created_doctor.id}, Name: {first_name} {last_name}")
            return created_doctor
        except ValueError as e: # Catch specific ValueError from repository.add (e.g. ID exists)
            logger.error(f"Error adding doctor to repository: {e}")
            raise InvalidOperationException(f"Could not create doctor: {e}")


    def get_doctor_by_id(self, doctor_id: UUID, include_deleted: bool = False) -> Optional[DoctorModel]:
        """Retrieves a doctor by their unique ID."""
        logger.debug(f"Fetching doctor by ID: {doctor_id}, include_deleted: {include_deleted}")
        doctor = self.doctor_repository.get_by_id(doctor_id, include_deleted=include_deleted)
        if not doctor:
            logger.debug(f"Doctor with ID {doctor_id} not found or does not meet deletion criteria.")
        return doctor

    def get_all_doctors(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[DoctorModel]:
        """
        Retrieves all doctors, with pagination and option to include soft-deleted records.
        """
        logger.debug(f"Fetching all doctors. Skip: {skip}, Limit: {limit}, Include Deleted: {include_deleted}")
        return self.doctor_repository.get_all(skip=skip, limit=limit, include_deleted=include_deleted)

    def update_doctor(self, doctor_id: UUID, update_fields: dict) -> Optional[DoctorModel]:
        """
        Updates an existing doctor's information.
        """
        doctor_to_update = self.doctor_repository.get_by_id(doctor_id, include_deleted=False) # Ensure doctor is active
        if not doctor_to_update:
            # raise ResourceNotFoundException(resource_name="Active doctor", resource_id=doctor_id)
            # Consistent with get_by_id, router will handle None to 404.
            logger.warning(f"Update failed: Active doctor with ID {doctor_id} not found.")
            return None

        # If 'gender' is in update_fields (likely within biodata), ensure it's validated
        if 'biodata' in update_fields and 'gender' in update_fields['biodata']:
            try:
                GenderEnum(update_fields['biodata']['gender'])
            except ValueError:
                raise InvalidOperationException(f"Invalid gender value provided in update: {update_fields['biodata']['gender']}")
        
        # If emergency_contact is being set to null/None explicitly in update_fields,
        # Pydantic model_copy should handle it. If it's a dict, it's an update/replacement.
        # If emergency_contact is in update_fields and is a dict, but missing required sub-fields,
        # Pydantic will raise validation error when model_copy tries to create EmergencyContact.

        logger.info(f"Attempting to update doctor ID: {doctor_id} with data: {update_fields}")
        updated_doctor = self.doctor_repository.update(doctor_id, update_fields)
        if not updated_doctor:
            logger.warning(f"Doctor with ID {doctor_id} was not updated by repository.")
        return updated_doctor


    def soft_delete_doctor(self, doctor_id: UUID) -> Optional[DoctorModel]:
        """Soft deletes a doctor by their ID."""
        doctor = self.doctor_repository.get_by_id(doctor_id, include_deleted=True)
        if not doctor:
            raise ResourceNotFoundException(resource_name="Doctor", resource_id=doctor_id)
        
        if doctor.date_deleted is not None:
            logger.info(f"Doctor {doctor_id} is already soft-deleted.")
            # raise InvalidOperationException(f"Doctor with ID {doctor_id} is already deleted.")
            return doctor # Return existing state

        logger.info(f"Attempting to soft delete doctor ID: {doctor_id}")
        deleted_doctor = self.doctor_repository.soft_delete(doctor_id)
        if not deleted_doctor:
            logger.error(f"Soft delete failed unexpectedly for doctor {doctor_id} after existence check.")
            raise InvalidOperationException(f"Could not soft delete doctor {doctor_id}.")
        return deleted_doctor


    def restore_doctor(self, doctor_id: UUID) -> Optional[DoctorModel]:
        """Restores a soft-deleted doctor by their ID."""
        doctor = self.doctor_repository.get_by_id(doctor_id, include_deleted=True)
        if not doctor:
            raise ResourceNotFoundException(resource_name="Doctor", resource_id=doctor_id)

        if doctor.date_deleted is None:
            raise InvalidOperationException(f"Doctor with ID {doctor_id} is not deleted, cannot restore.")

        logger.info(f"Attempting to restore doctor ID: {doctor_id}")
        restored_doctor = self.doctor_repository.restore(doctor_id)
        if not restored_doctor:
            logger.error(f"Restore failed unexpectedly for doctor {doctor_id} after checks.")
            raise InvalidOperationException(f"Could not restore doctor {doctor_id}.")
        return restored_doctor


    def find_doctors_by_specialty(self, specialty: str) -> List[DoctorModel]:
        """Finds active doctors by their medical specialty."""
        logger.debug(f"Searching for doctors with specialty: {specialty}")
        return self.doctor_repository.find_by_specialty(specialty)