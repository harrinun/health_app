from typing import List, Optional
from uuid import UUID
from datetime import datetime

from health_app.utils.file_manager import FileManager
from health_app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentOut, AppointmentStatus

class AppointmentRepository:
    def __init__(self, file_path: str = "data/appointments.json"):
        self.file_manager = FileManager(file_path)

    def list_appointments(self, include_deleted: bool = False) -> List[AppointmentOut]:
        all_data = self.file_manager.read_data()
        return [
            AppointmentOut(**record)
            for record in all_data
            if include_deleted or record["date_deleted"] is None
        ]

    def get_appointment(self, appointment_id: UUID) -> Optional[AppointmentOut]:
        record = self.file_manager.find_by_id(appointment_id)
        if record and record["date_deleted"] is None:
            return AppointmentOut(**record)
        return None

    def create_appointment(self, appointment: AppointmentCreate) -> AppointmentOut:
        new_id = self.file_manager.generate_id()
        timestamp = datetime.now().astimezone().isoformat()
        new_record = {
            "id": str(new_id),
            "patient_id": str(appointment.patient_id),
            "doctor_id": str(appointment.doctor_id),
            "appointment_datetime": appointment.appointment_datetime.isoformat(),
            "status": appointment.status.value,
            "date_created": timestamp,
            "date_updated": timestamp,
            "date_deleted": None
        }
        self.file_manager.write_data(new_record)
        return AppointmentOut(**new_record)

    def update_appointment(self, appointment_id: UUID, updates: AppointmentUpdate) -> Optional[AppointmentOut]:
        record = self.file_manager.find_by_id(appointment_id)
        if not record or record["date_deleted"]:
            return None

        if updates.appointment_datetime is not None:
            record["appointment_datetime"] = updates.appointment_datetime.isoformat()
        if updates.status is not None:
            record["status"] = updates.status.value

        record["date_updated"] = datetime.now().astimezone().isoformat()
        self.file_manager.overwrite(record)
        return AppointmentOut(**record)

    def delete_appointment(self, appointment_id: UUID) -> bool:
        return self.file_manager.delete(appointment_id)
