from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
import logging 
from typing import List
from uuid import UUID


# Schemas
from ..schemas.patient_schema import (
    PatientCreateSchema,
    PatientUpdateSchema,
    PatientResponseSchema
)
# Service
from ..services.patient_service import PatientService
# Email utility for background task
from ..utils.mail_utils import send_patient_welcome_email
# Repository for dependency setup (PatientService needs PatientRepository)
from ..repository.patient_repository import PatientRepository
# from ..utils.file_manager import FileManager # <--- REMOVED THIS LINE

# Pathlib was used for APP_DIR_ROUTER logic, which is also removed as repository handles its paths
# from pathlib import Path 

logger = logging.getLogger("health_app.routers.patients_router") # Corrected logger name

# --- Router Setup ---
patients_router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input data"}, 
        status.HTTP_409_CONFLICT: {"description": "Conflict, e.g., resource already exists or concurrency issue"}
    }
)

# --- Dependency for PatientService ---
# This path logic for APP_DIR_ROUTER is generally not needed in the router
# if the repository itself correctly resolves its data file path.
# try:
#     APP_DIR_ROUTER = Path(__file__).resolve().parent.parent # health_app/
# except NameError:
#     current_dir_router = Path(".").resolve()
#     if (current_dir_router / "models").exists() and (current_dir_router / "repository").exists():
#         APP_DIR_ROUTER = current_dir_router
#     else:
#         APP_DIR_ROUTER = current_dir_router / "health_app"
# PATIENTS_JSON_PATH = APP_DIR_ROUTER / "data" / "patients.json" # Path not directly used here

_patient_repository_instance = PatientRepository() # Instantiated once when router module is loaded

def get_patient_service() -> PatientService:
    return PatientService(patient_repository=_patient_repository_instance)


# --- Path Operations ---

@patients_router.post("/", response_model=PatientResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_patient(
    patient_data: PatientCreateSchema, 
    background_tasks: BackgroundTasks, 
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Create a new patient.
    A welcome email will be sent as a background task if an email address is provided.
    """
    # Service layer raises custom exceptions (subclasses of HTTPException)
    created_patient = patient_service.create_patient(
        first_name=patient_data.biodata.first_name,
        last_name=patient_data.biodata.last_name,
        date_of_birth=patient_data.biodata.date_of_birth,
        gender_str=patient_data.biodata.gender.value, 
        phone_number=patient_data.contact_information.phone_number,
        email=patient_data.contact_information.email,
        address=patient_data.contact_information.address,
        emergency_full_name=patient_data.emergency_contact.full_name,
        emergency_relationship=patient_data.emergency_contact.relationship,
        emergency_phone_number=patient_data.emergency_contact.phone_number
    )
    
    if created_patient.contact_information and created_patient.contact_information.email:
        logger.info(f"Scheduling welcome email for patient {created_patient.id} to {created_patient.contact_information.email}")
        background_tasks.add_task(
            send_patient_welcome_email,
            created_patient.contact_information.email, 
            created_patient.biodata.first_name
        )
    else:
        logger.info(f"Patient {created_patient.id} created but no email address provided or found. Welcome email not sent.")
            
    return created_patient


@patients_router.get("/", response_model=List[PatientResponseSchema])
async def get_all_patients_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted records"),
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Retrieve a list of all patients.
    Supports pagination using `skip` and `limit` query parameters.
    """
    patients = patient_service.get_all_patients(skip=skip, limit=limit, include_deleted=include_deleted)
    return patients


@patients_router.get("/{patient_id}", response_model=PatientResponseSchema)
async def get_patient_by_id_route(
    patient_id: UUID, 
    include_deleted: bool = Query(False, description="Set to true to retrieve a soft-deleted patient"),
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Retrieve a specific patient by their unique ID.
    Can optionally include soft-deleted patients.
    """
    patient = patient_service.get_patient_by_id(patient_id, include_deleted=include_deleted)
    if not patient:
        # Service returns None if not found based on include_deleted criteria.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found.")
    return patient


@patients_router.put("/{patient_id}", response_model=PatientResponseSchema)
async def update_existing_patient(
    patient_id: UUID,
    patient_update_data: PatientUpdateSchema,
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Update an existing patient's information.
    Only fields provided in the request body will be updated.
    """
    update_data_dict = patient_update_data.model_dump(exclude_unset=True)
    
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # Service method will raise ResourceNotFoundException or InvalidOperationException if applicable
    updated_patient = patient_service.update_patient(patient_id, update_data_dict)
    
    if not updated_patient: # Should be covered by service exceptions, but as a fallback
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found or could not be updated.")
    return updated_patient


@patients_router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Soft delete a patient by their unique ID.
    """
    patient_service.soft_delete_patient(patient_id) # Service raises if not found/already deleted
    return None 


@patients_router.put("/{patient_id}/restore", response_model=PatientResponseSchema)
async def restore_deleted_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Restore a soft-deleted patient.
    """
    restored_patient = patient_service.restore_patient(patient_id) # Service raises if not found/not deleted
    return restored_patient
