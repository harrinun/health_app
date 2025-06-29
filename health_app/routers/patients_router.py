from fastapi import APIRouter, Depends, status, Query, BackgroundTasks, HTTPException
import logging
from typing import List, Annotated
from uuid import UUID

# Schemas
from ..schemas.patient_schema import (
    PatientCreateSchema,
    PatientUpdateSchema,
    PatientResponseSchema
)
# Service
from ..services.patient_service import PatientService
# Email utility
from ..utils.mail_utils import send_patient_welcome_email
# Import the new dependency provider
from ..dependencies import get_patient_service

logger = logging.getLogger("health_app.routers.patients_router")

# Router Setup
patients_router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Patient not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input data"},
        status.HTTP_409_CONFLICT: {"description": "Conflict or concurrency issue"}
    }
)

# Updated path operation with Annotated.

@patients_router.post("/", response_model=PatientResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_patient(
    patient_data: PatientCreateSchema,
    background_tasks: BackgroundTasks,
    patient_service: Annotated[PatientService, Depends(get_patient_service)]
):
    """
    Create a new patient.
    A welcome email will be sent as a background task if an email address is provided.
    The persistence layer (JSON or Database) is determined by the application's configuration.
    """
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
        logger.info(f"Scheduling welcome email for patient {created_patient.id}")
        background_tasks.add_task(
            send_patient_welcome_email,
            created_patient.contact_information.email,
            created_patient.biodata.first_name
        )
    
    return created_patient

@patients_router.get("/", response_model=List[PatientResponseSchema])
async def get_all_patients_list(
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_deleted: bool = Query(False)
):
    """Retrieve a list of all patients with pagination."""
    return patient_service.get_all_patients(skip=skip, limit=limit, include_deleted=include_deleted)

@patients_router.get("/{patient_id}", response_model=PatientResponseSchema)
async def get_patient_by_id_route(
    patient_id: UUID,
    patient_service: Annotated[PatientService, Depends(get_patient_service)],
    include_deleted: bool = Query(False)
):
    """Retrieve a specific patient by their unique ID."""
    patient = patient_service.get_patient_by_id(patient_id, include_deleted=include_deleted)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found.")
    return patient

@patients_router.put("/{patient_id}", response_model=PatientResponseSchema)
async def update_existing_patient(
    patient_id: UUID,
    patient_update_data: PatientUpdateSchema,
    patient_service: Annotated[PatientService, Depends(get_patient_service)]
):
    """Update an existing patient's information."""
    update_data_dict = patient_update_data.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    return patient_service.update_patient(patient_id, update_data_dict)

@patients_router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_patient(
    patient_id: UUID,
    patient_service: Annotated[PatientService, Depends(get_patient_service)]
):
    """Soft delete a patient by their unique ID."""
    patient_service.soft_delete_patient(patient_id)
    return None

@patients_router.put("/{patient_id}/restore", response_model=PatientResponseSchema)
async def restore_deleted_patient(
    patient_id: UUID,
    patient_service: Annotated[PatientService, Depends(get_patient_service)]
):
    """Restore a soft-deleted patient."""
    return patient_service.restore_patient(patient_id)
