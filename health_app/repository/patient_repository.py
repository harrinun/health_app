from pathlib import Path
from typing import Optional, List 

from .base_repository import BaseRepository
from ..models.patient_model import PatientModel 
from ..utils.file_manager import FileManager


# --- Configuration for Patient Data ---
# Construct the path to the data file.
# This assumes 'health_app/data/patients.json'
# __file__ -> health_app/repository/patient_repository.py
# .parent -> health_app/repository/
# .parent.parent -> health_app/ (This is our application directory)
try:
    APP_DIR = Path(__file__).resolve().parent.parent
except NameError:
    current_dir = Path(".").resolve()
    if (current_dir / "models").exists() and (current_dir / "repository").exists(): # Likely inside health_app
        APP_DIR = current_dir
    else: # Likely project root, health_app is a subdir
        APP_DIR = current_dir / "health_app"


DATA_FILE_PATH = APP_DIR / "data" / "patients.json"


class PatientRepository(BaseRepository[PatientModel]):
    """
    Repository for managing patient data.
    It inherits generic CRUD operations from BaseRepository and is configured
    for PatientModel and the patients.json file.
    """
    def __init__(self):
        """
        Initializes the PatientRepository.
        Sets up the FileManager for patients.json and passes it to the BaseRepository.
        """
        # Ensure the data directory and file exist, handled by FileManager constructor
        patient_file_manager = FileManager(file_path=DATA_FILE_PATH)
        
        # Call the constructor of the BaseRepository with the file manager
        # and the PatientModel class.
        super().__init__(file_manager=patient_file_manager, model_class=PatientModel)

    # --- Patient-Specific Methods ---
    # These methods provide functionality unique to patient management beyond generic CRUD.

    def find_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        """
        Finds an active patient by their unique folder number.

        Args:
            folder_number (str): The patient folder number to search for.

        Returns:
            Optional[PatientModel]: The patient model instance if an active patient
                                    is found, otherwise None.
        """
        # Use get_all from BaseRepository, which handles soft-delete filtering by default.
        all_active_patients = self.get_all(include_deleted=False) 
        for patient in all_active_patients:
            # Check if the patient has 'patient_folder_number' attribute
            if hasattr(patient, 'patient_folder_number') and patient.patient_folder_number == folder_number:
                return patient
        return None

    def find_by_last_name(self, last_name: str) -> List[PatientModel]:
        """
        Finds active patients by their last name (case-insensitive).

        Args:
            last_name (str): The last name to search for.

        Returns:
            List[PatientModel]: A list of active patient model instances matching the last name.
        """
        all_active_patients = self.get_all(include_deleted=False) # Use get_all to respect soft delete
        matched_patients: List[PatientModel] = []
        for patient in all_active_patients:
            # Assuming patient.biodata.last_name exists
            if hasattr(patient, 'biodata') and hasattr(patient.biodata, 'last_name'):
                if patient.biodata.last_name.lower() == last_name.lower():
                    matched_patients.append(patient)
        return matched_patients

    
