from typing import List, Optional
from uuid import UUID
from datetime import datetime
from health_app.utils.file_manager import FileManager
from health_app.schemas.medical_record import MedicalRecordBase

class MedicalRecordRepository:
    def __init__(self):
        self.file_path = "health_app/data/medical_records.json"
        self.manager = FileManager(self.file_path)

    def get_all(self) -> List[MedicalRecordBase]:
        data = self.manager.read_data()
        return [MedicalRecordBase(**item) for item in data if item.get("date_deleted") is None]

    def get_by_id(self, record_id: UUID) -> Optional[MedicalRecordBase]:
        record = self.manager.find_by_id(record_id)
        if record and record.get("date_deleted") is None:
            return MedicalRecordBase(**record)
        return None

    def get_by_patient_id(self, patient_id: UUID) -> List[MedicalRecordBase]:
        records = self.get_all()
        return [record for record in records if record.patient_id == patient_id]

    def create(self, data: dict) -> MedicalRecordBase:
        data["id"] = str(self.manager.generate_id())
        data["date_created"] = datetime.now().isoformat()
        data["date_updated"] = None
        data["date_deleted"] = None
        self.manager.write_data(data)
        return MedicalRecordBase(**data)

    def update(self, record_id: UUID, update_data: dict) -> Optional[MedicalRecordBase]:
        record = self.manager.find_by_id(record_id)
        if not record or record.get("date_deleted"):
            return None
        record.update(update_data)
        record["date_updated"] = datetime.now().isoformat()
        self.manager.overwrite(record_id, record)
        return MedicalRecordBase(**record)

    def delete(self, record_id: UUID) -> bool:
        return self.manager.soft_delete(record_id)
