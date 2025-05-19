from typing import List, Optional
from uuid import UUID
from health_app.repositories.medical_record_repository import MedicalRecordRepository
from health_app.repositories.patient_repository import PatientRepository
from health_app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordUpdate,
    MedicalRecordOut
)
from health_app.schemas.medical_record import MedicalRecord
from health_app.utils.exceptions import NotFoundException

class MedicalRecordService:
    def __init__(self):
        self.repository = MedicalRecordRepository()
        self.patient_repository = PatientRepository()

    def get_all_records(self) -> List[MedicalRecordOut]:
        return [MedicalRecordOut(**record.dict()) for record in self.repository.get_all()]

    def get_record_by_id(self, record_id: UUID) -> MedicalRecordOut:
        record = self.repository.get_by_id(record_id)
        if not record:
            raise NotFoundException("Medical record not found.")
        return MedicalRecordOut(**record.dict())

    def get_records_by_patient(self, patient_id: UUID) -> List[MedicalRecordOut]:
        if not self.patient_repository.get_by_id(patient_id):
            raise NotFoundException("Patient not found.")
        records = self.repository.get_by_patient_id(patient_id)
        return [MedicalRecordOut(**r.dict()) for r in records]

    def create_record(self, record_data: MedicalRecordCreate) -> MedicalRecordOut:
        if not self.patient_repository.get_by_id(record_data.patient_id):
            raise NotFoundException("Patient not found.")
        new_record = self.repository.create(record_data.dict())
        return MedicalRecordOut(**new_record.dict())

    def update_record(self, record_id: UUID, update_data: MedicalRecordUpdate) -> MedicalRecordOut:
        updated = self.repository.update(record_id, update_data.dict(exclude_unset=True))
        if not updated:
            raise NotFoundException("Medical record not found or already deleted.")
        return MedicalRecordOut(**updated.dict())

    def delete_record(self, record_id: UUID) -> dict:
        success = self.repository.delete(record_id)
        if not success:
            raise NotFoundException("Medical record not found or already deleted.")
        return {"message": "Medical record soft-deleted successfully"}
