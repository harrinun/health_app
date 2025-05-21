# health_app/repositories/base_repository.py
from typing import Type, Optional, Dict, Any
from uuid import UUID
from health_app.utils.file_manager import FileManager

class BaseRepository:
    def __init__(self, file_path: str, schema_class: Type):
        self.file_manager = FileManager(file_path)
        self.schema_class = schema_class

    def _apply_soft_delete_filter(self, data: list, include_deleted: bool) -> list:
        return [item for item in data if include_deleted or item.get("date_deleted") is None]

    def list(self, include_deleted=False) -> list:
        return [self.schema_class(**item) for item in 
                self._apply_soft_delete_filter(self.file_manager.read_data(), include_deleted)]

