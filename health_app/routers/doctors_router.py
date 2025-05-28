from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from uuid import UUID
import logging 

# Schemas
from ..schemas.doctor_schema import (
    DoctorCreateSchema,
    DoctorUpdateSchema,
    DoctorResponseSchema
)
# Service
from ..services.doctor_service import DoctorService
# Repository for dependency setup
from ..repository.doctor_repository import DoctorRepository
# Custom Exceptions (services will raise these, FastAPI handles them)
# from ..utils.exceptions import ResourceNotFoundException, InvalidOperationException

logger = logging.getLogger("health_app.routers.doctors_router")

# --- Router Setup ---
doctors_router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Doctor not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input or operation for doctor"},
        status.HTTP_409_CONFLICT: {"description": "Conflict error related to doctor resource"}
    }
)



_doctor_repository_instance = DoctorRepository() # DoctorRepository handles its own FileManager

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
    The service layer will handle business logic and raise appropriate exceptions.
    """
   
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

@doctors_router.get("/", response_model=List[DoctorResponseSchema])
async def get_all_doctors_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return per page."),
    include_deleted: bool = Query(False, description="Set to true to include soft-deleted doctor records."),
    specialty: Optional[str] = Query(None, description="Filter doctors by their medical specialty (case-insensitive)."),
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Retrieve a list of all doctors. Supports pagination and filtering by specialty.
    """
    if specialty:
        doctors = doctor_service.find_doctors_by_specialty(specialty)
        # Manual pagination for filtered results; ideally, service method supports pagination.
        paginated_doctors = doctors[skip : skip + limit] if limit is not None else doctors[skip:]
        return paginated_doctors
    else:
        doctors = doctor_service.get_all_doctors(skip=skip, limit=limit, include_deleted=include_deleted)
    return doctors

@doctors_router.get("/{doctor_id}", response_model=DoctorResponseSchema)
async def get_doctor_by_id_route(
    doctor_id: UUID,
    # Re-added include_deleted query parameter for consistency and functionality
    include_deleted: bool = Query(False, description="Set to true to retrieve a soft-deleted doctor."),
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Retrieve a specific doctor by their unique ID.
    Use the `include_deleted` query parameter to fetch soft-deleted records.
    """
    # Pass the include_deleted flag to the service method
    doctor = doctor_service.get_doctor_by_id(doctor_id, include_deleted=include_deleted)
    if not doctor:
        # Service returns None if not found based on include_deleted criteria.
        # Router raises a 404.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with ID {doctor_id} not found.")
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
    update_data_dict = doctor_update_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    # Service method is expected to raise custom exceptions for errors like not found or invalid operations.
    updated_doctor = doctor_service.update_doctor(doctor_id, update_data_dict)
    
    # If service returns None (e.g., active doctor not found for update and service doesn't raise), raise 404.
    if not updated_doctor: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor with ID {doctor_id} not found or could not be updated (e.g., inactive).")
    return updated_doctor

@doctors_router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_doctor(
    doctor_id: UUID,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Soft delete a doctor.
    """
    # Service method (soft_delete_doctor) is expected to raise ResourceNotFoundException
    # or InvalidOperationException if the doctor cannot be deleted (e.g., not found, already deleted).
    doctor_service.soft_delete_doctor(doctor_id)
    return None # For 204 No Content

@doctors_router.put("/{doctor_id}/restore", response_model=DoctorResponseSchema)
async def restore_deleted_doctor(
    doctor_id: UUID,
    doctor_service: DoctorService = Depends(get_doctor_service)
):
    """
    Restore a soft-deleted doctor.
    """
    # Service method (restore_doctor) is expected to raise ResourceNotFoundException
    # or InvalidOperationException if the doctor cannot be restored.
    restored_doctor = doctor_service.restore_doctor(doctor_id)
    return restored_doctor
