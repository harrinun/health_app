"""
JSON file-based implementation of the Patient Repository Interface.

This class handles all data operations for the Patient model using a JSON file
as the persistence layer. It inherits from the IPatientRepository to ensure
it adheres to the required contract.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from .patient_interface import IPatientRepository
from ..models.patient_model import PatientModel
from ..utils.file_manager import FileManager

logger = logging.getLogger(__name__)

# Configuration for Patient JSON Data
try:
    APP_DIR = Path(__file__).resolve().parent.parent
except NameError:
    APP_DIR = Path("health_app").resolve()

DATA_FILE_PATH = APP_DIR / "data" / "patients.json"

class PatientJsonRepository(IPatientRepository):
    """
    Patient Repository implementation for JSON file storage..
    """

    def __init__(self):
        """Initializes the repository with a file manager for patients.json."""
        self.file_manager = FileManager(file_path=DATA_FILE_PATH)
        self.model_class = PatientModel

    def _load_data(self) -> List[PatientModel]:
        """Loads and validates patient data from the JSON file."""
        raw_data = self.file_manager.read_data()
        return [self.model_class(**record) for record in raw_data]

    def _save_data(self, data: List[PatientModel]):
        """Serializes and saves patient data to the JSON file."""
        serializable_data = [item.model_dump(mode='json') for item in data]
        self.file_manager.write_data(serializable_data)

    def _find_item_index(self, item_id: UUID, data: List[PatientModel]) -> Optional[int]:
        """Finds the index of a patient by ID."""
        for index, item in enumerate(data):
            if item.id == item_id:
                return index
        return None
    
    def get_all_for_folder_number_generation(self) -> List[PatientModel]:
        """In JSON mode, this is the same as get_all(include_deleted=True)."""
        return self.get_all(include_deleted=True, limit=None)

    def get_all(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[PatientModel]:
        all_items = self._load_data()
        if not include_deleted:
            processed_items = [item for item in all_items if not item.date_deleted]
        else:
            processed_items = all_items
        
        paginated_items = processed_items[skip:]
        if limit is not None:
            paginated_items = paginated_items[:limit]
        return paginated_items

    def get_by_id(self, item_id: UUID, include_deleted: bool = False) -> Optional[PatientModel]:
        all_items = self._load_data()
        for item in all_items:
            if item.id == item_id:
                if include_deleted or not item.date_deleted:
                    return item
        return None

    def add(self, item_to_add: PatientModel) -> PatientModel:
        all_items = self._load_data()
        if any(item.id == item_to_add.id for item in all_items):
            raise ValueError(f"Item with ID {item_to_add.id} already exists.")
        
        all_items.append(item_to_add)
        self._save_data(all_items)
        return item_to_add

    def update(self, item_id: UUID, update_data: Dict[str, Any]) -> Optional[PatientModel]:
        all_items = self._load_data()
        item_index = self._find_item_index(item_id, all_items)
        if item_index is None:
            return None

        item_to_update = all_items[item_index]
        if item_to_update.date_deleted:
            logger.warning(f"Update failed: Item with ID {item_id} is soft-deleted.")
            return None

        update_payload = update_data.copy()
        update_payload['date_updated'] = datetime.now(timezone.utc)
        
        updated_item = item_to_update.model_copy(update=update_payload)
        all_items[item_index] = updated_item
        self._save_data(all_items)
        return updated_item

    def soft_delete(self, item_id: UUID) -> Optional[PatientModel]:
        return self._toggle_delete_status(item_id, is_deleting=True)

    def restore(self, item_id: UUID) -> Optional[PatientModel]:
        return self._toggle_delete_status(item_id, is_deleting=False)

    def _toggle_delete_status(self, item_id: UUID, is_deleting: bool) -> Optional[PatientModel]:
        all_items = self._load_data()
        item_index = self._find_item_index(item_id, all_items)
        if item_index is None: return None

        item = all_items[item_index]
        now = datetime.now(timezone.utc)
        
        if is_deleting: # Soft delete
            if item.date_deleted: return item # Already deleted
            update_values = {'date_deleted': now, 'date_updated': now}
        else: # Restore
            if not item.date_deleted: return item # Already active
            update_values = {'date_deleted': None, 'date_updated': now}

        updated_item = item.model_copy(update=update_values)
        all_items[item_index] = updated_item
        self._save_data(all_items)
        return updated_item
        
    def find_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        all_active_patients = self.get_all(include_deleted=False)
        for patient in all_active_patients:
            if patient.patient_folder_number == folder_number:
                return patient
        return None

    def find_by_last_name(self, last_name: str) -> List[PatientModel]:
        all_active_patients = self.get_all(include_deleted=False)
        return [p for p in all_active_patients if p.biodata.last_name.lower() == last_name.lower()]
