"""
FastAPI Dependency Injection Providers.

This module contains functions that will be used with `Depends()` to provide
dependencies (like repositories or services) to the application's path operations.

The key benefit is that it decouples the application's business logic from the
concrete implementation of its dependencies.
"""
import logging
from typing import Annotated, Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from .config import settings
from .database.config import get_db
from .repository.patient_interface import IPatientRepository
from .repository.patient_sql_repository import PatientSqlRepository
from .repository.patient_json_repository import PatientJsonRepository
from .services.patient_service import PatientService

logger = logging.getLogger(__name__)



def get_patient_repository(db: Annotated[Session, Depends(get_db)]) -> Generator[IPatientRepository, None, None]:
    """
    Dependency provider for the patient repository.

    This function reads the `PERSISTENCE_MODE` from the settings and returns
    an instance of the appropriate repository (SQL or JSON).
    It now creates the repository on-demand in BOTH cases.
    """
    mode = settings.PERSISTENCE_MODE
    logger.debug(f"Providing patient repository in '{mode}' mode.")
    
    if mode == "database":
        # This behavior is unchanged: create a new SQL repo for each request.
        yield PatientSqlRepository(db)
    elif mode == "json":
        # UPDATED: We now create a NEW instance of the JSON repository here.
        # This ensures that we don't use a stale, cached singleton instance.
        yield PatientJsonRepository()
    else:
        raise ValueError(f"Unknown persistence mode: {mode}")

# Service Provider

def get_patient_service(
    repo: Annotated[IPatientRepository, Depends(get_patient_repository)]
) -> PatientService:
    """
    Dependency provider for the patient service.
    """
    return PatientService(patient_repository=repo)
