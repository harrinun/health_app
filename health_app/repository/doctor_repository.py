from pathlib import Path
from typing import List # For type hinting

# Assuming BaseRepository, DoctorModel, and FileManager are correctly importable
# from their respective locations.
# Adjust these imports if your actual file structure differs.
from .base_repository import BaseRepository
from ..models.doctor_model import DoctorModel # Specific model for this repository
from ..utils.file_manager import FileManager

# --- Configuration for Doctor Data ---
# Construct the path to the data file: health_app/data/doctors.json
try:
    # __file__ is health_app/repository/doctor_repository.py
    # .parent is health_app/repository/
    # .parent.parent is health_app/ (This is our application directory)
    APP_DIR = Path(__file__).resolve().parent.parent
except NameError:
    # Fallback for environments where __file__ might not be defined.
    current_dir = Path(".").resolve()
    # A simple check to see if we are likely in health_app or project_root
    if (current_dir / "models").exists() and (current_dir / "repository").exists():
        APP_DIR = current_dir # Likely CWD is health_app
    else:
        APP_DIR = current_dir / "health_app" # Assume CWD is project root

DATA_FILE_PATH = APP_DIR / "data" / "doctors.json"


class DoctorRepository(BaseRepository[DoctorModel]):
    """
    Repository for managing doctor data.
    Inherits generic CRUD operations from BaseRepository, configured for DoctorModel.
    """
    def __init__(self):
        """
        Initializes the DoctorRepository.
        Sets up the FileManager for doctors.json and passes it to BaseRepository.
        """
        doctor_file_manager = FileManager(file_path=DATA_FILE_PATH)
        super().__init__(file_manager=doctor_file_manager, model_class=DoctorModel)

    # --- Doctor-Specific Methods ---

    def find_by_specialty(self, specialty: str) -> List[DoctorModel]:
        """
        Finds active doctors by their medical specialty (case-insensitive).

        Args:
            specialty (str): The medical specialty to search for.

        Returns:
            List[DoctorModel]: A list of active doctor model instances matching the specialty.
        """
        all_active_doctors = self.get_all(include_deleted=False) 
        
        matched_doctors: List[DoctorModel] = []
        for doctor in all_active_doctors:
            if hasattr(doctor, 'specialty') and doctor.specialty.lower() == specialty.lower():
                matched_doctors.append(doctor)
        return matched_doctors

    def find_by_experience_greater_than(self, years: int) -> List[DoctorModel]:
        """
        Finds active doctors with years of experience greater than the specified value.
    
        Args:
            years (int): The minimum number of years of experience.
    
        Returns:
            List[DoctorModel]: A list of active doctors meeting the criteria.
        """
        all_active_doctors = self.get_all(include_deleted=False)
        experienced_doctors: List[DoctorModel] = []
        for doctor in all_active_doctors:
            if hasattr(doctor, 'years_of_experience') and doctor.years_of_experience > years:
                experienced_doctors.append(doctor)
        return experienced_doctors