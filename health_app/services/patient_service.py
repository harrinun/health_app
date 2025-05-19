from typing import List, Optional
from datetime import datetime, timezone

from health_app.repositories.patient_repository import PatientRepository
from health_app.schemas.patient import PatientCreate, PatientUpdate, PatientOut


class PatientService:
    def __init__(self):
        self.repository = PatientRepository()

    def create_patient(self, data: PatientCreate) -> PatientOut:
        all_patients = self.repository.get_all()

        # Optional business rule: prevent duplicate by name + phone
        for patient in all_patients:
            if (
                patient["first_name"].lower() == data.first_name.lower()
                and patient["last_name"].lower() == data.last_name.lower()
                and patient["contact"]["phone"] == data.contact.phone
            ):
                raise ValueError("Patient with same name and phone already exists.")

        created_patient = self.repository.create(data.dict())
        return PatientOut(**created_patient)

    def list_patients(self, page: int = 1, page_size: int = 10) -> List[PatientOut]:
        all_data = self.repository.get_all()
        active = [p for p in all_data if p.get("date_deleted") is None]

        start = (page - 1) * page_size
        end = start + page_size
        return [PatientOut(**p) for p in active[start:end]]

    def get_patient(self, patient_id: str) -> Optional[PatientOut]:
        data = self.repository.get_by_id(patient_id)
        if data and data.get("date_deleted") is None:
            return PatientOut(**data)
        return None

    def update_patient(self, patient_id: str, update_data: PatientUpdate) -> Optional[PatientOut]:
        update_dict = update_data.dict(exclude_unset=True)
        update_dict["date_updated"] = datetime.now(timezone.utc).isoformat()
        updated = self.repository.update(patient_id, update_dict)
        if updated and updated.get("date_deleted") is None:
            return PatientOut(**updated)
        return None

    def delete_patient(self, patient_id: str) -> bool:
        return self.repository.soft_delete(patient_id)
