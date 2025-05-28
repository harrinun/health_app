from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from ..models.appointment_model import AppointmentModel
from ..models.enums import AppointmentStatusEnum
from ..repository.appointment_repository import AppointmentRepository
from ..repository.patient_repository import PatientRepository 
from ..repository.doctor_repository import DoctorRepository 
from ..utils.exceptions import ( # Import custom exceptions
    ResourceNotFoundException,
    InvalidOperationException,
    DoctorUnavailableException
)
import logging

logger = logging.getLogger(__name__)

class AppointmentService:
    """
    Service layer for managing appointments.
    Contains business logic related to appointment operations,
    such as checking doctor availability.
    """
    def __init__(
        self, 
        appointment_repository: AppointmentRepository,
        patient_repository: PatientRepository, 
        doctor_repository: DoctorRepository    
    ):
        self.appointment_repository = appointment_repository
        self.patient_repository = patient_repository
        self.doctor_repository = doctor_repository

    def create_appointment(
        self,
        patient_id: UUID,
        doctor_id: UUID,
        appointment_date_time_utc: datetime, 
        notes: Optional[str] = None
    ) -> AppointmentModel:
        if not isinstance(appointment_date_time_utc, datetime):
            raise InvalidOperationException("appointment_date_time_utc must be a valid datetime object.")

        if appointment_date_time_utc.tzinfo is None:
            logger.warning("create_appointment received a naive datetime for appointment_date_time_utc. Assuming UTC.")
            appointment_date_time_utc = appointment_date_time_utc.replace(tzinfo=timezone.utc)
            
        if appointment_date_time_utc <= datetime.now(timezone.utc):
            logger.error(f"Attempt to create appointment in the past: {appointment_date_time_utc}")
            raise InvalidOperationException("Appointment date and time must be in the future.")

        patient = self.patient_repository.get_by_id(patient_id, include_deleted=False) # Check for active patient
        if not patient:
            logger.error(f"Failed to create appointment: Active patient with ID {patient_id} not found.")
            # Check if patient exists at all to differentiate "not found" vs "inactive"
            if not self.patient_repository.get_by_id(patient_id, include_deleted=True):
                raise ResourceNotFoundException(resource_name="Patient", resource_id=patient_id)
            else:
                raise InvalidOperationException(f"Patient with ID {patient_id} is inactive and cannot have new appointments.")


        doctor = self.doctor_repository.get_by_id(doctor_id, include_deleted=False) # Check for active doctor
        if not doctor:
            logger.error(f"Failed to create appointment: Active doctor with ID {doctor_id} not found.")
            if not self.doctor_repository.get_by_id(doctor_id, include_deleted=True):
                raise ResourceNotFoundException(resource_name="Doctor", resource_id=doctor_id)
            else:
                raise InvalidOperationException(f"Doctor with ID {doctor_id} is inactive and cannot be assigned new appointments.")


        existing_appointment = self.appointment_repository.find_doctor_appointment_at_time(
            doctor_id=doctor_id,
            appointment_time=appointment_date_time_utc
        )
        if existing_appointment:
            logger.error(f"Doctor {doctor_id} is unavailable at {appointment_date_time_utc}. Conflicting appointment: {existing_appointment.id}")
            raise DoctorUnavailableException(doctor_id=doctor_id, appointment_time=appointment_date_time_utc)

        new_appointment = AppointmentModel(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date_time=appointment_date_time_utc,
            notes=notes,
            status=AppointmentStatusEnum.SCHEDULED 
        )
        
        try:
            created_appointment = self.appointment_repository.add(new_appointment)
            logger.info(f"Appointment scheduled for patient {patient_id} with doctor {doctor_id} at {appointment_date_time_utc}. ID: {created_appointment.id}")
            return created_appointment
        except ValueError as e: # From repository.add if ID somehow clashes
            logger.error(f"Error adding appointment to repository: {e}")
            raise InvalidOperationException(f"Could not create appointment: {e}")


    def get_appointment_by_id(self, appointment_id: UUID, include_deleted: bool = False) -> Optional[AppointmentModel]:
        logger.debug(f"Fetching appointment by ID: {appointment_id}, include_deleted: {include_deleted}")
        appointment = self.appointment_repository.get_by_id(appointment_id, include_deleted=include_deleted)
        if not appointment:
            logger.debug(f"Appointment with ID {appointment_id} not found or does not meet deletion criteria.")
        return appointment

    def get_all_appointments(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[AppointmentModel]:
        logger.debug(f"Fetching all appointments. Skip: {skip}, Limit: {limit}, Include Deleted: {include_deleted}")
        return self.appointment_repository.get_all(skip=skip, limit=limit, include_deleted=include_deleted)

    def update_appointment_details(self, appointment_id: UUID, update_fields: dict) -> Optional[AppointmentModel]:
        if "patient_id" in update_fields or "doctor_id" in update_fields:
            logger.error("Attempt to update patient_id or doctor_id via update_appointment_details.")
            raise InvalidOperationException("Patient ID and Doctor ID cannot be changed after appointment creation.")
        
        appointment_to_update = self.appointment_repository.get_by_id(appointment_id, include_deleted=False)
        if not appointment_to_update:
            # raise ResourceNotFoundException(resource_name="Active appointment", resource_id=appointment_id)
            logger.warning(f"Update failed: Active appointment with ID {appointment_id} not found.")
            return None

        if 'appointment_date_time' in update_fields:
            new_time_utc = update_fields['appointment_date_time']
            if not isinstance(new_time_utc, datetime):
                 raise InvalidOperationException("Invalid format for appointment_date_time.")
            if new_time_utc.tzinfo is None:
                logger.warning("update_appointment_details received a naive datetime for new time. Assuming UTC.")
                new_time_utc = new_time_utc.replace(tzinfo=timezone.utc)
            update_fields['appointment_date_time'] = new_time_utc

            if new_time_utc <= datetime.now(timezone.utc):
                raise InvalidOperationException("New appointment date and time must be in the future.")

            if new_time_utc != appointment_to_update.appointment_date_time:
                conflicting_appointment = self.appointment_repository.find_doctor_appointment_at_time(
                    doctor_id=appointment_to_update.doctor_id, 
                    appointment_time=new_time_utc
                )
                if conflicting_appointment and conflicting_appointment.id != appointment_id: 
                    raise DoctorUnavailableException(doctor_id=appointment_to_update.doctor_id, appointment_time=new_time_utc)
        
        logger.info(f"Attempting to update appointment ID: {appointment_id} with details: {update_fields}")
        updated_appointment = self.appointment_repository.update(appointment_id, update_fields)
        if not updated_appointment:
            logger.warning(f"Appointment with ID {appointment_id} was not updated by repository.")
        return updated_appointment


    def change_appointment_status(self, appointment_id: UUID, new_status: AppointmentStatusEnum, notes: Optional[str] = None) -> Optional[AppointmentModel]:
        appointment = self.appointment_repository.get_by_id(appointment_id, include_deleted=False)
        if not appointment:
            # raise ResourceNotFoundException(resource_name="Active appointment", resource_id=appointment_id)
            logger.warning(f"Cannot change status: Active appointment ID {appointment_id} not found.")
            return None
        
        # More Business logic for status transitions will be added
        # e.g., cannot change a 'COMPLETED' appointment back to 'SCHEDULED' without specific permissions/logic etc.

        update_payload = {"status": new_status}
        if notes is not None:
            current_notes = appointment.notes or ""
            separator = "\n---\n" if current_notes.strip() else "" 
            timestamp_note = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
            update_payload["notes"] = f"{current_notes}{separator}Status changed to {new_status.value} on {timestamp_note}. Notes: {notes}"
        
        logger.info(f"Changing status of appointment ID {appointment_id} to {new_status.value}")
        updated_appointment = self.appointment_repository.update(appointment_id, update_payload)
        if not updated_appointment:
            logger.warning(f"Appointment status for ID {appointment_id} was not updated by repository.")
        return updated_appointment


    def soft_delete_appointment(self, appointment_id: UUID) -> Optional[AppointmentModel]:
        appointment = self.appointment_repository.get_by_id(appointment_id, include_deleted=True)
        if not appointment:
            raise ResourceNotFoundException(resource_name="Appointment", resource_id=appointment_id)
        
        if appointment.date_deleted is not None:
            logger.info(f"Appointment {appointment_id} is already soft-deleted.")
            return appointment 

        logger.info(f"Attempting to soft delete appointment ID: {appointment_id}")
        deleted_appointment = self.appointment_repository.soft_delete(appointment_id)
        if not deleted_appointment:
            logger.error(f"Soft delete failed unexpectedly for appointment {appointment_id} after existence check.")
            raise InvalidOperationException(f"Could not soft delete appointment {appointment_id}.")
        return deleted_appointment

    def restore_appointment(self, appointment_id: UUID) -> Optional[AppointmentModel]:
        appointment = self.appointment_repository.get_by_id(appointment_id, include_deleted=True)
        if not appointment:
            raise ResourceNotFoundException(resource_name="Appointment", resource_id=appointment_id)

        if appointment.date_deleted is None:
            raise InvalidOperationException(f"Appointment with ID {appointment_id} is not deleted, cannot restore.")

        logger.info(f"Attempting to restore appointment ID: {appointment_id}")
        restored_appointment = self.appointment_repository.restore(appointment_id)
        if not restored_appointment:
            logger.error(f"Restore failed unexpectedly for appointment {appointment_id} after checks.")
            raise InvalidOperationException(f"Could not restore appointment {appointment_id}.")
        return restored_appointment

    def get_appointments_for_patient(self, patient_id: UUID, include_deleted: bool = False) -> List[AppointmentModel]:
        logger.debug(f"Fetching appointments for patient ID: {patient_id}")
        return self.appointment_repository.find_by_patient_id(patient_id, include_deleted)

    def get_appointments_for_doctor(self, doctor_id: UUID, include_deleted: bool = False) -> List[AppointmentModel]:
        logger.debug(f"Fetching appointments for doctor ID: {doctor_id}")
        return self.appointment_repository.find_by_doctor_id(doctor_id, include_deleted)

    def get_appointments_by_status(self, status: AppointmentStatusEnum, include_deleted: bool = False) -> List[AppointmentModel]:
        logger.debug(f"Fetching appointments with status: {status.value}")
        return self.appointment_repository.find_by_status(status, include_deleted)

    def get_appointments_in_date_range(self, start_datetime: datetime, end_datetime: datetime, include_deleted: bool = False) -> List[AppointmentModel]:
        logger.debug(f"Fetching appointments between {start_datetime} and {end_datetime}")
        return self.appointment_repository.find_by_date_range(start_datetime, end_datetime, include_deleted)

