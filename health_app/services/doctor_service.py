from typing import List, Optional
from datetime import datetime, timezone

from health_app.repositories.doctor_repository import DoctorRepository
from health_app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut


class DoctorService:
    def __init__(self):
        self.repository = DoctorRepository()

    def create_doctor(self, data: DoctorCreate) -> DoctorOut:
        all_doctors = self.repository.get_all()

        # Optional: Prevent duplicate doctor by name + email
        for doc in all_doctors:
            if (
                doc["first_name"].lower() == data.first_name.lower()
                and doc["last_name"].lower() == data.last_name.lower()
                and doc["email"].lower() == data.email.lower()
            ):
                raise ValueError("Doctor with same name and email already exists.")

        created = self.repository.create(data.dict())
        return DoctorOut(**created)

    def list_doctors(self, page: int = 1, page_size: int = 10) -> List[DoctorOut]:
        all_data = self.repository.get_all()
        active = [d for d in all_data if d.get("date_deleted") is None]

        start = (page - 1) * page_size
        end = start + page_size
        return [DoctorOut(**d) for d in active[start:end]]

    def get_doctor(self, doctor_id: str) -> Optional[DoctorOut]:
        data = self.repository.get_by_id(doctor_id)
        if data and data.get("date_deleted") is None:
            return DoctorOut(**data)
        return None

    def update_doctor(self, doctor_id: str, update_data: DoctorUpdate) -> Optional[DoctorOut]:
        update_dict = update_data.dict(exclude_unset=True)
        update_dict["date_updated"] = datetime.now(timezone.utc).isoformat()
        updated = self.repository.update(doctor_id, update_dict)
        if updated and updated.get("date_deleted") is None:
            return DoctorOut(**updated)
        return None

    def delete_doctor(self, doctor_id: str) -> bool:
        return self.repository.soft_delete(doctor_id)
