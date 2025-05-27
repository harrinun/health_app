from fastapi import APIRouter, HTTPException, Depends, status, Query
from pathlib import Path
from typing import List, Optional
from uuid import UUID

# Schemas
from ..schemas.doctor_schema import (
    DoctorCreateSchema,
    DoctorUpdateSchema,
    DoctorResponseSchema
)
# Service
from ..services.doctor_service import DoctorService
# Repository and FileManager for dependency setup
from ..repository.doctor_repository import DoctorRepository


# --- Router Setup ---
doctors_router = APIRouter( # Renamed APIRouter instance
    prefix="/doctors",
    tags=["Doctors"],
    responses={404: {"description": "Doctor not found"}}
)

# --- Dependency for DoctorService ---
try:
    APP_DIR_DOCTOR_ROUTER = Path(__file__).resolve().parent.parent # health_app/
except NameError:
    current_dir_router = Path(".").resolve()
    if (current_dir_router / "models").exists() and (current_dir_router / "repository").exists():
        APP_DIR_DOCTOR_ROUTER = current_dir_router
    else:
        APP_DIR_DOCTOR_ROUTER = current_dir_router / "health_app"
# DOCTORS_JSON_PATH = APP_DIR_DOCTOR_ROUTER / "data" / "doctors.json" # Path not directly used here

_doctor_repository_instance = DoctorRepository()

def get_doctor_service() -> DoctorService:
    return DoctorService(doctor_repository=_doctor_repository_instance)

# --- Path Operations ---

@doctors_router.post("/", response_model=DoctorResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_doctor(
    doctor_data: DoctorCreateSchema,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Create a new doctor.
    """
    try:
        created_doctor = doctor_service.create_doctor(
            first_name=doctor_data.biodata.first_name,
            last_name=doctor_data.biodata.last_name,
            date_of_birth=doctor_data.biodata.date_of_birth,
            gender_str=doctor_data.biodata.gender.value,
            specialty=doctor_data.specialty,
            years_of_experience=doctor_data.years_of_experience,
            phone_number=doctor_data.contact_information.phone_number,
            email=doctor_data.contact_information.email,
            address=doctor_data.contact_information.address,
            emergency_full_name=doctor_data.emergency_contact.full_name if doctor_data.emergency_contact else None,
            emergency_relationship=doctor_data.emergency_contact.relationship if doctor_data.emergency_contact else None,
            emergency_phone_number=doctor_data.emergency_contact.phone_number if doctor_data.emergency_contact else None
        )
        return created_doctor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the doctor.")

@doctors_router.get("/", response_model=List[DoctorResponseSchema])
async def get_all_doctors_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_deleted: bool = Query(False),
    specialty: Optional[str] = Query(None, description="Filter doctors by specialty"),
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Retrieve a list of all doctors. Supports pagination and filtering by specialty.
    """
    if specialty:
        doctors = doctor_service.find_doctors_by_specialty(specialty)
        # Manual pagination for filtered results
        return doctors[skip : skip + limit] if limit else doctors[skip:]
    else:
        doctors = doctor_service.get_all_doctors(skip=skip, limit=limit, include_deleted=include_deleted)
    return doctors

@doctors_router.get("/{doctor_id}", response_model=DoctorResponseSchema)
async def get_doctor_by_id_route(
    doctor_id: UUID,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Retrieve a specific doctor by their unique ID.
    """
    doctor = doctor_service.get_doctor_by_id(doctor_id)
    if not doctor or (doctor.date_deleted is not None and not include_deleted): # Adjusted logic
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found or inactive.")
    return doctor

@doctors_router.put("/{doctor_id}", response_model=DoctorResponseSchema)
async def update_existing_doctor(
    doctor_id: UUID,
    doctor_update_data: DoctorUpdateSchema,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Update an existing doctor's information.
    """
    try:
        update_data_dict = doctor_update_data.model_dump(exclude_unset=True)
        if not update_data_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
        
        updated_doctor = doctor_service.update_doctor(doctor_id, update_data_dict)
        if not updated_doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found or could not be updated.")
        return updated_doctor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the doctor.")

@doctors_router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_doctor(
    doctor_id: UUID,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Soft delete a doctor.
    """
    deleted_doctor = doctor_service.soft_delete_doctor(doctor_id)
    if not deleted_doctor:
        existing = doctor_service.get_doctor_by_id(doctor_id=doctor_id, include_deleted=True)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
    return None

@doctors_router.put("/{doctor_id}/restore", response_model=DoctorResponseSchema)
async def restore_deleted_doctor(
    doctor_id: UUID,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Restore a soft-deleted doctor.
    """
    restored_doctor = doctor_service.restore_doctor(doctor_id)
    if not restored_doctor:
        existing = doctor_service.get_doctor_by_id(doctor_id=doctor_id, include_deleted=True)
        if not existing:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")
        if existing.date_deleted is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Doctor is not deleted.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not restore doctor.")
    return restored_doctor