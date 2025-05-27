from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date, datetime, timezone

from ..models.medical_record_model import MedicalRecordModel
from ..repository.medical_record_repository import MedicalRecordRepository
from ..repository.patient_repository import PatientRepository 
from ..repository.doctor_repository import DoctorRepository 
from ..repository.appointment_repository import AppointmentRepository 
from ..utils.exceptions import ( # Import custom exceptions
    ResourceNotFoundException,
    InvalidOperationException
)
import logging

logger = logging.getLogger(__name__)

class MedicalRecordService:
    """
    Service layer for managing medical records.
    Contains business logic related to medical record operations.
    """
    def __init__(
        self,
        medical_record_repository: MedicalRecordRepository,
        patient_repository: PatientRepository,
        doctor_repository: Optional[DoctorRepository] = None, 
        appointment_repository: Optional[AppointmentRepository] = None 
    ):
        self.medical_record_repository = medical_record_repository
        self.patient_repository = patient_repository
        self.doctor_repository = doctor_repository
        self.appointment_repository = appointment_repository

    def create_medical_record(
        self,
        patient_id: UUID,
        diagnosis: str,
        treatment_date: date, 
        prescriptions: Optional[List[str]] = None,
        doctor_notes: Optional[str] = None,
        attending_doctor_id: Optional[UUID] = None,
        appointment_id: Optional[UUID] = None
    ) -> MedicalRecordModel:
        # 1. Validate patient existence (must be active)
        patient = self.patient_repository.get_by_id(patient_id, include_deleted=False)
        if not patient:
            logger.error(f"Failed to create medical record: Active patient with ID {patient_id} not found.")
            if not self.patient_repository.get_by_id(patient_id, include_deleted=True): # Check if exists at all
                raise ResourceNotFoundException(resource_name="Patient", resource_id=patient_id)
            else:
                raise InvalidOperationException(f"Patient with ID {patient_id} is inactive. Cannot create medical record.")

        # 2. Validate attending_doctor_id if provided (must be active)
        if attending_doctor_id and self.doctor_repository:
            doctor = self.doctor_repository.get_by_id(attending_doctor_id, include_deleted=False)
            if not doctor:
                logger.error(f"Failed to create medical record: Active attending doctor with ID {attending_doctor_id} not found.")
                if not self.doctor_repository.get_by_id(attending_doctor_id, include_deleted=True):
                    raise ResourceNotFoundException(resource_name="Attending doctor", resource_id=attending_doctor_id)
                else:
                    raise InvalidOperationException(f"Attending doctor with ID {attending_doctor_id} is inactive.")
        elif attending_doctor_id and not self.doctor_repository:
             logger.warning("Attending doctor ID provided but no doctor repository configured in service.")


        # 3. Validate appointment_id if provided (must be active and belong to the patient)
        if appointment_id and self.appointment_repository:
            appointment = self.appointment_repository.get_by_id(appointment_id, include_deleted=False)
            if not appointment:
                logger.error(f"Failed to create medical record: Active appointment with ID {appointment_id} not found.")
                if not self.appointment_repository.get_by_id(appointment_id, include_deleted=True):
                     raise ResourceNotFoundException(resource_name="Appointment", resource_id=appointment_id)
                else:
                    raise InvalidOperationException(f"Appointment with ID {appointment_id} is inactive.")
            
            if appointment.patient_id != patient_id:
                logger.error(f"Failed to create medical record: Appointment {appointment_id} (patient {appointment.patient_id}) does not belong to patient {patient_id}.")
                raise InvalidOperationException(f"Appointment {appointment_id} does not belong to patient {patient_id}.")
        elif appointment_id and not self.appointment_repository:
            logger.warning("Appointment ID provided but no appointment repository configured in service.")


        new_record = MedicalRecordModel(
            patient_id=patient_id,
            diagnosis=diagnosis,
            prescriptions=prescriptions if prescriptions is not None else [],
            treatment_date=treatment_date,
            doctor_notes=doctor_notes,
            attending_doctor_id=attending_doctor_id,
            appointment_id=appointment_id
        )
        
        try:
            created_record = self.medical_record_repository.add(new_record)
            logger.info(f"Medical record created for patient ID: {patient_id}. Record ID: {created_record.id}")
            return created_record
        except ValueError as e: # From repository.add if ID somehow clashes
            logger.error(f"Error adding medical record to repository: {e}")
            raise InvalidOperationException(f"Could not create medical record: {e}")


    def get_medical_record_by_id(self, record_id: UUID, include_deleted: bool = False) -> Optional[MedicalRecordModel]:
        logger.debug(f"Fetching medical record by ID: {record_id}, include_deleted: {include_deleted}")
        record = self.medical_record_repository.get_by_id(record_id, include_deleted=include_deleted)
        if not record:
            logger.debug(f"Medical record with ID {record_id} not found or does not meet deletion criteria.")
        return record

    def get_all_medical_records(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[MedicalRecordModel]:
        logger.debug(f"Fetching all medical records. Skip: {skip}, Limit: {limit}, Include Deleted: {include_deleted}")
        return self.medical_record_repository.get_all(skip=skip, limit=limit, include_deleted=include_deleted)

    def update_medical_record(self, record_id: UUID, update_fields: dict) -> Optional[MedicalRecordModel]:
        if "patient_id" in update_fields:
            logger.error("Attempt to update patient_id via update_medical_record.")
            raise InvalidOperationException("Patient ID cannot be changed for an existing medical record.")

        existing_record = self.medical_record_repository.get_by_id(record_id, include_deleted=False)
        if not existing_record:
            # raise ResourceNotFoundException(resource_name="Active medical record", resource_id=record_id)
            logger.warning(f"Update failed: Active medical record with ID {record_id} not found.")
            return None

        # Validate attending_doctor_id if being updated and repository exists
        if "attending_doctor_id" in update_fields and update_fields["attending_doctor_id"] is not None and self.doctor_repository:
            doctor_id_to_check = update_fields["attending_doctor_id"]
            doctor = self.doctor_repository.get_by_id(doctor_id_to_check, include_deleted=False) # Check active
            if not doctor:
                if not self.doctor_repository.get_by_id(doctor_id_to_check, include_deleted=True):
                    raise ResourceNotFoundException(resource_name="Attending doctor", resource_id=doctor_id_to_check)
                else:
                    raise InvalidOperationException(f"Attending doctor with ID {doctor_id_to_check} is inactive.")


        # Validate appointment_id if being updated and repository exists
        if "appointment_id" in update_fields and update_fields["appointment_id"] is not None and self.appointment_repository:
            appointment_id_to_check = update_fields["appointment_id"]
            appointment = self.appointment_repository.get_by_id(appointment_id_to_check, include_deleted=False) # Check active
            if not appointment:
                if not self.appointment_repository.get_by_id(appointment_id_to_check, include_deleted=True):
                    raise ResourceNotFoundException(resource_name="Appointment", resource_id=appointment_id_to_check)
                else:
                    raise InvalidOperationException(f"Appointment with ID {appointment_id_to_check} is inactive.")
            
            if appointment.patient_id != existing_record.patient_id: # Ensure new appointment belongs to the same patient
                raise InvalidOperationException(f"New appointment {appointment_id_to_check} patient ID ({appointment.patient_id}) does not match medical record's patient ID ({existing_record.patient_id}).")


        logger.info(f"Attempting to update medical record ID: {record_id} with data: {update_fields}")
        updated_record = self.medical_record_repository.update(record_id, update_fields)
        if not updated_record:
             logger.warning(f"Medical record with ID {record_id} was not updated by repository.")
        return updated_record


    def soft_delete_medical_record(self, record_id: UUID) -> Optional[MedicalRecordModel]:
        record = self.medical_record_repository.get_by_id(record_id, include_deleted=True)
        if not record:
            raise ResourceNotFoundException(resource_name="Medical record", resource_id=record_id)
        
        if record.date_deleted is not None:
            logger.info(f"Medical record {record_id} is already soft-deleted.")
            return record 

        logger.info(f"Attempting to soft delete medical record ID: {record_id}")
        deleted_record = self.medical_record_repository.soft_delete(record_id)
        if not deleted_record:
            logger.error(f"Soft delete failed unexpectedly for medical record {record_id} after existence check.")
            raise InvalidOperationException(f"Could not soft delete medical record {record_id}.")
        return deleted_record

    def restore_medical_record(self, record_id: UUID) -> Optional[MedicalRecordModel]:
        record = self.medical_record_repository.get_by_id(record_id, include_deleted=True)
        if not record:
            raise ResourceNotFoundException(resource_name="Medical record", resource_id=record_id)

        if record.date_deleted is None:
            raise InvalidOperationException(f"Medical record with ID {record_id} is not deleted, cannot restore.")

        logger.info(f"Attempting to restore medical record ID: {record_id}")
        restored_record = self.medical_record_repository.restore(record_id)
        if not restored_record:
            logger.error(f"Restore failed unexpectedly for medical record {record_id} after checks.")
            raise InvalidOperationException(f"Could not restore medical record {record_id}.")
        return restored_record

    def get_medical_records_for_patient(self, patient_id: UUID, include_deleted: bool = False) -> List[MedicalRecordModel]:
        logger.debug(f"Fetching medical records for patient ID: {patient_id}")
        # Validate patient exists before attempting to fetch records? Optional, repo might just return empty list.
        # patient = self.patient_repository.get_by_id(patient_id, include_deleted=True)
        # if not patient:
        #     raise ResourceNotFoundException(resource_name="Patient", resource_id=patient_id)
        return self.medical_record_repository.find_by_patient_id(patient_id, include_deleted)
        
    def get_medical_records_by_attending_doctor(self, doctor_id: UUID, include_deleted: bool = False) -> List[MedicalRecordModel]:
        logger.debug(f"Fetching medical records for attending doctor ID: {doctor_id}")
        if self.doctor_repository: # Check if doctor repo is available for validation
            doctor = self.doctor_repository.get_by_id(doctor_id, include_deleted=True)
            if not doctor:
                # Depending on desired strictness, either raise ResourceNotFoundException or return empty list.
                # For a "find by" operation, returning an empty list if the doctor doesn't exist is often acceptable.
                logger.info(f"Attending doctor with ID {doctor_id} not found. Returning empty list of medical records.")
                return []
        else:
            logger.warning("Doctor repository not available for find_by_attending_doctor_id validation.")
        return self.medical_record_repository.find_by_attending_doctor_id(doctor_id, include_deleted)

    def get_medical_records_by_treatment_date(self, treatment_date: date, include_deleted: bool = False) -> List[MedicalRecordModel]:
        logger.debug(f"Fetching medical records for treatment date: {treatment_date}")
        return self.medical_record_repository.find_by_treatment_date(treatment_date, include_deleted)
