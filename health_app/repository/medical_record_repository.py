from pathlib import Path # Already imported
from typing import List # Already imported
from uuid import UUID # Already imported
from datetime import date # For filtering by treatment date


from .base_repository import BaseRepository
from ..models.medical_record_model import MedicalRecordModel 
from ..utils.file_manager import FileManager

# --- Configuration for Medical Record Data ---
# Construct the path to the data file: health_app/data/medical_records.json
try:
    APP_DIR_MEDICAL_RECORD = Path(__file__).resolve().parent.parent # Renamed to avoid clash
except NameError:
    current_dir_medical_record = Path(".").resolve()
    if (current_dir_medical_record / "models").exists() and (current_dir_medical_record / "repository").exists():
        APP_DIR_MEDICAL_RECORD = current_dir_medical_record
    else:
        APP_DIR_MEDICAL_RECORD = current_dir_medical_record / "health_app"

DATA_FILE_PATH_MEDICAL_RECORD = APP_DIR_MEDICAL_RECORD / "data" / "medical_records.json"


class MedicalRecordRepository(BaseRepository[MedicalRecordModel]):
    """
    Repository for managing medical record data.
    Inherits generic CRUD operations from BaseRepository, configured for MedicalRecordModel.
    """
    def __init__(self):
        """
        Initializes the MedicalRecordRepository.
        Sets up the FileManager for medical_records.json and passes it to BaseRepository.
        """
        medical_record_file_manager = FileManager(file_path=DATA_FILE_PATH_MEDICAL_RECORD)
        super().__init__(file_manager=medical_record_file_manager, model_class=MedicalRecordModel)

    # --- Medical Record-Specific Methods ---

    def find_by_patient_id(self, patient_id: UUID, include_deleted: bool = False) -> List[MedicalRecordModel]:
        all_records = self.get_all(include_deleted=include_deleted)
        return [record for record in all_records if hasattr(record, 'patient_id') and record.patient_id == patient_id]

    def find_by_treatment_date(self, treatment_date: date, include_deleted: bool = False) -> List[MedicalRecordModel]:
        all_records = self.get_all(include_deleted=include_deleted)
        return [record for record in all_records if hasattr(record, 'treatment_date') and record.treatment_date == treatment_date]
        
    def find_by_attending_doctor_id(self, doctor_id: UUID, include_deleted: bool = False) -> List[MedicalRecordModel]:
        all_records = self.get_all(include_deleted=include_deleted)
        return [
            record for record in all_records 
            if hasattr(record, 'attending_doctor_id') and record.attending_doctor_id == doctor_id
        ]
