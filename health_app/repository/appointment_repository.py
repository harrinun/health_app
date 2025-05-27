from pathlib import Path # Already imported, but good for clarity per file
from typing import List, Optional # Already imported, but good for clarity per file
from uuid import UUID
from datetime import datetime

# Assuming BaseRepository, AppointmentModel, AppointmentStatusEnum, FileManager
# are correctly importable
from .base_repository import BaseRepository
from ..models.appointment_model import AppointmentModel # Specific model
from ..models.enums import AppointmentStatusEnum # For status-based filtering
from ..utils.file_manager import FileManager

# --- Configuration for Appointment Data ---
# Construct the path to the data file: health_app/data/appointments.json
try:
    APP_DIR_APPOINTMENT = Path(__file__).resolve().parent.parent # Renamed to avoid clash if in same execution scope
except NameError:
    current_dir_appointment = Path(".").resolve()
    if (current_dir_appointment / "models").exists() and (current_dir_appointment / "repository").exists():
        APP_DIR_APPOINTMENT = current_dir_appointment
    else:
        APP_DIR_APPOINTMENT = current_dir_appointment / "health_app"

DATA_FILE_PATH_APPOINTMENT = APP_DIR_APPOINTMENT / "data" / "appointments.json"


class AppointmentRepository(BaseRepository[AppointmentModel]):
    """
    Repository for managing appointment data.
    Inherits generic CRUD operations from BaseRepository, configured for AppointmentModel.
    """
    def __init__(self):
        """
        Initializes the AppointmentRepository.
        Sets up the FileManager for appointments.json and passes it to BaseRepository.
        """
        appointment_file_manager = FileManager(file_path=DATA_FILE_PATH_APPOINTMENT)
        super().__init__(file_manager=appointment_file_manager, model_class=AppointmentModel)

    # --- Appointment-Specific Methods ---

    def find_by_patient_id(self, patient_id: UUID, include_deleted: bool = False) -> List[AppointmentModel]:
        all_appointments = self.get_all(include_deleted=include_deleted)
        return [appt for appt in all_appointments if hasattr(appt, 'patient_id') and appt.patient_id == patient_id]

    def find_by_doctor_id(self, doctor_id: UUID, include_deleted: bool = False) -> List[AppointmentModel]:
        all_appointments = self.get_all(include_deleted=include_deleted)
        return [appt for appt in all_appointments if hasattr(appt, 'doctor_id') and appt.doctor_id == doctor_id]

    def find_by_date_range(self, start_datetime: datetime, end_datetime: datetime, include_deleted: bool = False) -> List[AppointmentModel]:
        all_appointments = self.get_all(include_deleted=include_deleted)
        return [
            appt for appt in all_appointments 
            if hasattr(appt, 'appointment_date_time') and start_datetime <= appt.appointment_date_time <= end_datetime
        ]
        
    def find_by_status(self, status: AppointmentStatusEnum, include_deleted: bool = False) -> List[AppointmentModel]:
        all_appointments = self.get_all(include_deleted=include_deleted)
        return [appt for appt in all_appointments if hasattr(appt, 'status') and appt.status == status]

    def find_doctor_appointment_at_time(self, doctor_id: UUID, appointment_time: datetime) -> Optional[AppointmentModel]:
        doctor_appointments = self.get_all(include_deleted=False) 
        for appointment in doctor_appointments:
            if appointment.doctor_id == doctor_id and \
               appointment.appointment_date_time == appointment_time and \
               appointment.status not in [AppointmentStatusEnum.CANCELLED, AppointmentStatusEnum.COMPLETED]:
                return appointment
        return None