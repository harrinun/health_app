"""
Defines the interface (Abstract Base Class) for the Patient Repository.

This ensures that any concrete patient repository implementation (e.g., for JSON or SQL)
will have the same methods allowing them to be used interchangeably by the service layer.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..models.patient_model import PatientModel

class IPatientRepository(ABC):
    """
    Interface for patient data persistence operations.
    """

    @abstractmethod
    def get_all(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[PatientModel]:
        """Retrieves a list of patients with pagination and soft-delete filtering."""
        pass

    @abstractmethod
    def get_by_id(self, item_id: UUID, include_deleted: bool = False) -> Optional[PatientModel]:
        """Retrieves a single patient by their unique ID."""
        pass

    @abstractmethod
    def add(self, item_to_add: PatientModel) -> PatientModel:
        """Adds a new patient to the data store."""
        pass

    @abstractmethod
    def update(self, item_id: UUID, update_data: Dict[str, Any]) -> Optional[PatientModel]:
        """Updates an existing patient's data."""
        pass

    @abstractmethod
    def soft_delete(self, item_id: UUID) -> Optional[PatientModel]:
        """Marks a patient as deleted without permanently removing them."""
        pass
    
    @abstractmethod
    def restore(self, item_id: UUID) -> Optional[PatientModel]:
        """Restores a soft-deleted patient."""
        pass

    @abstractmethod
    def find_by_folder_number(self, folder_number: str) -> Optional[PatientModel]:
        """Finds an active patient by their folder number."""
        pass

    @abstractmethod
    def find_by_last_name(self, last_name: str) -> List[PatientModel]:
        """Finds active patients by their last name."""
        pass
    
    @abstractmethod
    def get_all_for_folder_number_generation(self) -> List[PatientModel]:
        """A specific method to get all patients (including deleted) for folder number generation."""
        pass
