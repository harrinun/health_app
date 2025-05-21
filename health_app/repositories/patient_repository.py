from health_app.utils.file_manager import FileManager
from datetime import datetime, timezone
from typing import Optional, List, Dict
import json
from uuid import UUID
from health_app.repositories.base_repository import BaseRepository
from health_app.schemas.patient import PatientOut


class PatientRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            file_path="health_app/data/patients.json",
            schema_class=PatientOut
        )
    
    def create(self, data: dict) -> PatientOut:
        data["id"] = str(uuid.uuid4())
        data["date_created"] = datetime.now(timezone.utc).isoformat()
        all_data = self.file_manager.read_all()
        all_data.append(data)
        self.file_manager.write_all(all_data)
        return self.schema_class(**data)

    def get_all(self) -> List[Dict]:
        return self.file_manager.read_data()

    def get_by_id(self, patient_id: str) -> Optional[Dict]:
        return self.file_manager.find_by_id(patient_id)

    def update(self, patient_id: str, updates: Dict) -> Optional[Dict]:
        existing = self.get_by_id(patient_id)
        if not existing:
            return None
        self.file_manager.update(patient_id, updates)
        return self.get_by_id(patient_id)

    def soft_delete(self, patient_id: str) -> bool:
        if self.get_by_id(patient_id):
            self.file_manager.delete(patient_id)
            return True
        return False


def custom_json_serializer(obj):
    if isinstance(obj, (datetime, UUID)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# When saving data to JSON
with open(self.file_path, "w") as f:
    json.dump(data, f, default=custom_json_serializer, indent=2)