from health_app.utils.file_manager import FileManager
from datetime import datetime, timezone
from typing import Optional, List, Dict
import json
from uuid import UUID



class PatientRepository:
    def __init__(self):
        self.file_manager = FileManager("data/patients.json")

    def create(self, patient_data: Dict) -> Dict:
        patient_data["id"] = self.file_manager.generate_id()
        patient_data["date_created"] = datetime.now(timezone.utc).isoformat()
        patient_data["date_updated"] = None
        patient_data["date_deleted"] = None
        self.file_manager.save(patient_data)
        return patient_data

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