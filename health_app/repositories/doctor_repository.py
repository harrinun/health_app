from health_app.utils.file_manager import FileManager
from datetime import datetime, timezone
from typing import Optional, List, Dict


class DoctorRepository:
    def __init__(self):
        self.file_manager = FileManager("data/doctors.json")

    def create(self, doctor_data: Dict) -> Dict:
        doctor_data["id"] = self.file_manager.generate_id()
        doctor_data["date_created"] = datetime.now(timezone.utc).isoformat()
        doctor_data["date_updated"] = None
        doctor_data["date_deleted"] = None
        self.file_manager.save(doctor_data)
        return doctor_data

    def get_all(self) -> List[Dict]:
        return self.file_manager.read_data()

    def get_by_id(self, doctor_id: str) -> Optional[Dict]:
        return self.file_manager.find_by_id(doctor_id)

    def update(self, doctor_id: str, updates: Dict) -> Optional[Dict]:
        existing = self.get_by_id(doctor_id)
        if not existing:
            return None
        self.file_manager.update(doctor_id, updates)
        return self.get_by_id(doctor_id)

    def soft_delete(self, doctor_id: str) -> bool:
        if self.get_by_id(doctor_id):
            self.file_manager.delete(doctor_id)
            return True
        return False
