import json
from uuid import UUID
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid


def custom_json_serializer(obj):
    if isinstance(obj, (datetime, UUID)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class FileManager:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.write_data([])  # Initialize with empty list

    def read_data(self, include_deleted=False) -> List[Dict[str, Any]]:
        with self.file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not include_deleted:
            data = [record for record in data if record.get("date_deleted") is None]
        return data

    def write_data(self, data: List[Dict[str, Any]]):
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=custom_json_serializer)


    def generate_id(self) -> str:
        return str(uuid.uuid4())

    def find_by_id(self, record_id: str, include_deleted=False) -> Optional[Dict[str, Any]]:
        for record in self.read_data(include_deleted=include_deleted):
            if record["id"] == record_id:
                return record
        return None

    def save(self, record: Dict[str, Any]):
        data = self.read_data(include_deleted=True)
        data.append(record)
        self.write_data(data)

    def update(self, record_id: str, updates: Dict[str, Any]):
        data = self.read_data(include_deleted=True)
        for record in data:
            if record["id"] == record_id:
                record.update(updates)
                record["date_updated"] = datetime.now(timezone.utc).isoformat()
                break
        self.write_data(data)

    def delete(self, record_id: str):
        data = self.read_data(include_deleted=True)
        for record in data:
            if record["id"] == record_id:
                record["date_deleted"] = datetime.now(timezone.utc).isoformat()
                break
        self.write_data(data)