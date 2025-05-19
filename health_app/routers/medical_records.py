from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from health_app.repositories.medical_record_repository import MedicalRecordRepository
from health_app.repositories.patient_repository import PatientRepository
from health_app.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordOut
from health_app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])

service = None  # Will be initialized after the class definition


class MedicalRecordService:
    def __init__(self):
        self.repository = MedicalRecordRepository()
        self.patient_repository = PatientRepository()

    def get_all_records(self) -> List[MedicalRecordOut]:
        return [MedicalRecordOut(**record) for record in self.repository.get_all()]

    def get_record_by_id(self, record_id: UUID) -> MedicalRecordOut:
        record = self.repository.get_by_id(record_id)
        if not record:
            raise NotFoundException("Medical record not found.")
        return MedicalRecordOut(**record)

    def get_records_by_patient(self, patient_id: UUID) -> List[MedicalRecordOut]:
        if not self.patient_repository.get_by_id(patient_id):
            raise NotFoundException("Patient not found.")
        records = self.repository.get_by_patient_id(patient_id)
        return [MedicalRecordOut(**r) for r in records]

    def create_record(self, record_data: MedicalRecordCreate) -> MedicalRecordOut:
        if not self.patient_repository.get_by_id(record_data.patient_id):
            raise NotFoundException("Patient not found.")
        new_record = self.repository.create(record_data.model_dump())
        return MedicalRecordOut(**new_record)

    def update_record(self, record_id: UUID, update_data: MedicalRecordUpdate) -> MedicalRecordOut:
        updated = self.repository.update(record_id, update_data.model_dump(exclude_unset=True))
        if not updated:
            raise NotFoundException("Medical record not found or already deleted.")
        return MedicalRecordOut(**updated)

    def delete_record(self, record_id: UUID) -> dict:
        success = self.repository.delete(record_id)
        if not success:
            raise NotFoundException("Medical record not found or already deleted.")
        return {"message": "Medical record soft-deleted successfully"}


# Initialize the service
service = MedicalRecordService()

# ----------------------------
# FastAPI Route Definitions
# ----------------------------

@router.get("/", response_model=List[MedicalRecordOut])
def list_medical_records():
    return service.get_all_records()

@router.get("/{record_id}", response_model=MedicalRecordOut)
def get_record(record_id: UUID):
    return service.get_record_by_id(record_id)

@router.get("/patient/{patient_id}", response_model=List[MedicalRecordOut])
def get_records_by_patient(patient_id: UUID):
    return service.get_records_by_patient(patient_id)

@router.post("/", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
def create_record(record_data: MedicalRecordCreate):
    return service.create_record(record_data)

@router.put("/{record_id}", response_model=MedicalRecordOut)
def update_record(record_id: UUID, update_data: MedicalRecordUpdate):
    return service.update_record(record_id, update_data)

@router.delete("/{record_id}")
def delete_record(record_id: UUID):
    return service.delete_record(record_id)
