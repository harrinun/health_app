from typing import List, Optional
from uuid import UUID
from datetime import datetime

from health_app.repositories.appointment_repository import AppointmentRepository
from health_app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentOut,
    AppointmentStatus,
)

class AppointmentService:
    def __init__(self):
        self.repository = AppointmentRepository()

    def list_appointments(
        self, status: Optional[AppointmentStatus] = None, date: Optional[datetime] = None
    ) -> List[AppointmentOut]:
        appointments = self.repository.list_appointments()
        if status:
            appointments = [appt for appt in appointments if appt.status == status]
        if date:
            appointments = [
                appt for appt in appointments
                if appt.appointment_datetime.date() == date.date()
            ]
        return appointments

    def get_appointment(self, appointment_id: UUID) -> Optional[AppointmentOut]:
        return self.repository.get_appointment(appointment_id)

    def create_appointment(self, appointment: AppointmentCreate) -> AppointmentOut:
        # Check for overlapping appointment for doctor
        existing = self.repository.list_appointments()
        for appt in existing:
            if (
                appt.doctor_id == appointment.doctor_id
                and appt.appointment_datetime == appointment.appointment_datetime
                and appt.status == AppointmentStatus.scheduled
            ):
                raise ValueError("Doctor already has an appointment at this time.")
        return self.repository.create_appointment(appointment)

    def update_appointment(
        self, appointment_id: UUID, updates: AppointmentUpdate
    ) -> Optional[AppointmentOut]:
        # Enforce check if changing datetime
        if updates.appointment_datetime:
            current = self.repository.get_appointment(appointment_id)
            if not current:
                return None
            existing = self.repository.list_appointments()
            for appt in existing:
                if (
                    appt.doctor_id == current.doctor_id
                    and appt.id != appointment_id
                    and appt.appointment_datetime == updates.appointment_datetime
                    and appt.status == AppointmentStatus.scheduled
                ):
                    raise ValueError("Doctor already has another appointment at this new time.")
        return self.repository.update_appointment(appointment_id, updates)

    def delete_appointment(self, appointment_id: UUID) -> bool:
        return self.repository.delete_appointment(appointment_id)
