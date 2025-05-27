from fastapi import APIRouter, HTTPException, Depends, status, Query # Re-import for clarity
from typing import List, Optional # Re-import for clarity
from uuid import UUID # Re-import for clarity
from datetime import datetime # Re-import for clarity

# Schemas
from ..schemas.appointment_schema import (
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    AppointmentResponseSchema
)
from ..models.enums import AppointmentStatusEnum # For query param
# Services
from ..services.appointment_service import AppointmentService
# Repositories for service dependencies
from ..repository.appointment_repository import AppointmentRepository
from ..repository.patient_repository import PatientRepository as ApptPatientRepo 
from ..repository.doctor_repository import DoctorRepository as ApptDoctorRepo   

# --- Router Setup ---
appointments_router = APIRouter( # Renamed APIRouter instance
    prefix="/appointments",
    tags=["Appointments"],
    responses={404: {"description": "Appointment not found"}}
)

# --- Dependency for AppointmentService ---
_appt_repository_instance = AppointmentRepository()
_appt_patient_repo_instance = ApptPatientRepo() 
_appt_doctor_repo_instance = ApptDoctorRepo()   

def get_appointment_service() -> AppointmentService:
    return AppointmentService(
        appointment_repository=_appt_repository_instance,
        patient_repository=_appt_patient_repo_instance, 
        doctor_repository=_appt_doctor_repo_instance    
    )

# --- Path Operations ---

@appointments_router.post("/", response_model=AppointmentResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_appointment(
    appointment_data: AppointmentCreateSchema,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Create a new appointment.
    Checks for doctor availability and validity of patient/doctor IDs.
    """
    try:
        created_appointment = appointment_service.create_appointment(
            patient_id=appointment_data.patient_id,
            doctor_id=appointment_data.doctor_id,
            appointment_date_time_utc=appointment_data.appointment_date_time,
            notes=appointment_data.notes
        )
        return created_appointment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the appointment.")


@appointments_router.get("/", response_model=List[AppointmentResponseSchema])
async def get_all_appointments_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_deleted: bool = Query(False),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    doctor_id: Optional[UUID] = Query(None, description="Filter by doctor ID"),
    status_filter: Optional[AppointmentStatusEnum] = Query(None, alias="status", description="Filter by appointment status"), # Changed alias for clarity
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format) for appointment_date_time"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format) for appointment_date_time"),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Retrieve a list of appointments with various filtering options and pagination.
    """
    if patient_id:
        appointments = appointment_service.get_appointments_for_patient(patient_id, include_deleted)
    elif doctor_id:
        appointments = appointment_service.get_appointments_for_doctor(doctor_id, include_deleted)
    elif status_filter:
        appointments = appointment_service.get_appointments_by_status(status_filter, include_deleted)
    elif start_date and end_date:
        appointments = appointment_service.get_appointments_in_date_range(start_date, end_date, include_deleted)
    else:
        appointments = appointment_service.get_all_appointments(skip=skip, limit=limit, include_deleted=include_deleted)
        return appointments 
    
    # Manual pagination for filtered results
    if limit:
        return appointments[skip : skip + limit]
    return appointments[skip:]


@appointments_router.get("/{appointment_id}", response_model=AppointmentResponseSchema)
async def get_appointment_by_id_route(
    appointment_id: UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted record") # Allow fetching soft-deleted if specified
):
    """
    Retrieve a specific appointment by ID.
    """
    appointment = appointment_service.get_appointment_by_id(appointment_id) # Service get_by_id should handle include_deleted if needed, or repo does. BaseRepo's get_by_id takes it.
    # For router, let's assume service get_by_id only returns active unless told otherwise.
    # Re-checking: AppointmentService.get_appointment_by_id does not take include_deleted.
    # We need to adjust either the service or this endpoint.
    # For now, let's rely on the default behavior (active only) from service.
    if not appointment: # If service returns None
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    if appointment.date_deleted is not None and not include_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment is inactive.")
    return appointment

@appointments_router.put("/{appointment_id}", response_model=AppointmentResponseSchema)
async def update_existing_appointment(
    appointment_id: UUID,
    appointment_update_data: AppointmentUpdateSchema,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Update an existing appointment's time, status, or notes.
    """
    try:
        update_data_dict = appointment_update_data.model_dump(exclude_unset=True)
        if not update_data_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
        
        updated_appointment: Optional[AppointmentModel] = None
        
        # Handle status change and other updates separately
        new_status = update_data_dict.pop("status", None)
        notes_for_status_change = update_data_dict.pop("notes", None) # Pop notes to avoid double application if status changes too

        if update_data_dict: # If there are other fields to update (e.g. appointment_date_time)
            # Note: update_appointment_details in service might also take notes.
            # If notes are only for status change, this logic needs care.
            # Let's assume notes from schema can update general notes.
            if notes_for_status_change and not new_status : # Notes provided but no status change
                update_data_dict['notes'] = notes_for_status_change

            updated_appointment = appointment_service.update_appointment_details(appointment_id, update_data_dict)

        if new_status:
            # If update_appointment_details was called and successful, use that as base for status change
            # If only status change, updated_appointment would be None here
            # This ensures that timestamp is updated once correctly.
            current_notes_for_status = appointment_update_data.notes # Original notes from schema for status change
            updated_appointment = appointment_service.change_appointment_status(appointment_id, new_status, current_notes_for_status)
        
        if not updated_appointment: # If no update operation was effectively performed or failed
            # Check if appointment exists if no update was made
            if not appointment_service.get_appointment_by_id(appointment_id):
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
            # If only status was in payload and it was already that status, service might return existing.
            # Or if update_data_dict was empty after popping status.
            # Re-fetch to be sure what to return if no error but no update.
            # This logic could be simplified if the service methods are more atomic or the PUT is more constrained.
            # For now, if updated_appointment is None after trying, assume failure or no change needed.
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment could not be updated or no changes detected.")

        return updated_appointment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the appointment.")


@appointments_router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_appointment(
    appointment_id: UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Soft delete an appointment.
    """
    deleted_appointment = appointment_service.soft_delete_appointment(appointment_id)
    if not deleted_appointment:
        existing = appointment_service.get_appointment_by_id(appointment_id=appointment_id, include_deleted=True)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    return None

@appointments_router.put("/{appointment_id}/restore", response_model=AppointmentResponseSchema)
async def restore_deleted_appointment(
    appointment_id: UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Restore a soft-deleted appointment.
    """
    restored_appointment = appointment_service.restore_appointment(appointment_id)
    if not restored_appointment:
        existing = appointment_service.get_appointment_by_id(appointment_id=appointment_id, include_deleted=True)
        if not existing:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
        if existing.date_deleted is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment is not deleted.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not restore appointment.")
    return restored_appointment
