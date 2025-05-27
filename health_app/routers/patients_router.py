from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks # Added BackgroundTasks
from typing import List, Optional
from uuid import UUID
import logging # Added for logging

# Schemas
from ..schemas.patient_schema import (
    PatientCreateSchema,
    PatientUpdateSchema,
    PatientResponseSchema
)
# Service
from ..services.patient_service import PatientService
# Email utility for background task
from ..utils.mail_utils import send_patient_welcome_email # Added email sending function
# Repository for dependency setup (PatientService needs PatientRepository)
from ..repository.patient_repository import PatientRepository

logger = logging.getLogger("health_app.routers.patients") # Specific logger for this router

# --- Router Setup ---
# Ensuring the APIRouter instance is named 'patients_router' for consistency with main.py import
patients_router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    responses={
        404: {"description": "Patient not found"},
        400: {"description": "Invalid input data"}, # Added for potential ValueError/InvalidOperationException
        409: {"description": "Conflict, e.g., resource already exists or concurrency issue"} # Added for ConcurrencyException
    }
)

# --- Dependency for PatientService ---
# This approach creates a new repository instance per service instance,
# which in turn creates a new FileManager. This is simple but might not be
# the most efficient for resource use if you had a real DB connection.
# For file-based, it's generally fine.
_patient_repository_instance = PatientRepository() # Instantiated once when router module is loaded

def get_patient_service() -> PatientService:
    # Consider if _patient_repository_instance should be created here for per-request or managed differently.
    # For simplicity and current file-based backend, module-level instance is okay.
    return PatientService(patient_repository=_patient_repository_instance)


# --- Path Operations ---

@patients_router.post("/", response_model=PatientResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_patient(
    patient_data: PatientCreateSchema, # FastAPI handles Pydantic validation from this schema
    background_tasks: BackgroundTasks, # FastAPI will inject this
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Create a new patient.
    A welcome email will be sent as a background task if an email address is provided.
    - **biodata**: Patient's biographical information.
    - **contact_information**: Patient's contact details.
    - **emergency_contact**: Patient's emergency contact.
    The `patient_folder_number` is generated automatically.
    """
    # The PatientService's create_patient method will raise custom exceptions
    # (ResourceNotFoundException, InvalidOperationException, ConcurrencyException)
    # which inherit from HTTPException. FastAPI's default error handling or our
    # custom handlers in main.py will manage these.
    
    # Aligning with PatientService.create_patient signature:
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
    
    # Add email sending to background tasks if email is available
    if created_patient.contact_information and created_patient.contact_information.email:
        logger.info(f"Scheduling welcome email for patient {created_patient.id} to {created_patient.contact_information.email}")
        background_tasks.add_task(
            send_patient_welcome_email,
            created_patient.contact_information.email, # Pass the EmailStr object
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
    patient_service: PatientService = Depends(get_patient_service),
    include_deleted: bool = Query(False, description="Set to true to retrieve a soft-deleted patient") # Added query param
):
    """
    Retrieve a specific patient by their unique ID.
    Can optionally include soft-deleted patients.
    """
    patient = patient_service.get_patient_by_id(patient_id, include_deleted=include_deleted)
    if not patient:
        # If include_deleted was true and still not found, it truly doesn't exist.
        # If include_deleted was false and not found, it might be soft-deleted or not exist.
        # The service layer's get_by_id handles this logic by returning None.
        detail_msg = "Patient not found"
        if not include_deleted:
            detail_msg += " or is inactive. Try with 'include_deleted=true' if you suspect it's soft-deleted."
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail_msg)
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
    
    # The service returns None if the patient was not found for update (e.g., already soft-deleted).
    # If the service raises ResourceNotFoundException directly, this check might not be needed.
    # Based on PatientService.update_patient, it returns None if active patient not found.
    if not updated_patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found or cannot be updated (e.g., inactive).")
    return updated_patient


@patients_router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Soft delete a patient by their unique ID.
    The patient record is marked as deleted but not permanently removed.
    Returns HTTP 204 No Content on successful deletion.
    """
    # PatientService.soft_delete_patient raises ResourceNotFoundException if not found
    # or InvalidOperationException if already deleted (or returns existing if we change that behavior).
    patient_service.soft_delete_patient(patient_id)
    return None # For 204 No Content, don't return a body.


@patients_router.put("/{patient_id}/restore", response_model=PatientResponseSchema)
async def restore_deleted_patient(
    patient_id: UUID,
    patient_service: PatientService = Depends(get_patient_service)
):
    """
    Restore a soft-deleted patient.
    """
    # PatientService.restore_patient raises ResourceNotFoundException or InvalidOperationException
    restored_patient = patient_service.restore_patient(patient_id)
    return restored_patient

