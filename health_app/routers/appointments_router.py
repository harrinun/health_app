from fastapi import APIRouter, HTTPException, Depends, status, Query 
from typing import List, Optional 
from uuid import UUID 
from datetime import datetime 
import logging 

# Schemas
from ..schemas.appointment_schema import (
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    AppointmentResponseSchema
)
from ..models.enums import AppointmentStatusEnum 
# Services
from ..services.appointment_service import AppointmentService
# Repositories for service dependencies
from ..repository.appointment_repository import AppointmentRepository
from ..repository.patient_repository import PatientRepository as ApptPatientRepo 
from ..repository.doctor_repository import DoctorRepository as ApptDoctorRepo   
# Import the model for type hinting
from ..models.appointment_model import AppointmentModel 

logger_appointments = logging.getLogger("health_app.routers.appointments_router") 

# --- Router Setup ---
appointments_router = APIRouter( 
    prefix="/appointments",
    tags=["Appointments"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Appointment not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input or operation for appointment"},
        status.HTTP_409_CONFLICT: {"description": "Conflict error (e.g., doctor unavailable)"}
    }
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
    created_appointment = appointment_service.create_appointment(
        patient_id=appointment_data.patient_id,
        doctor_id=appointment_data.doctor_id,
        appointment_date_time_utc=appointment_data.appointment_date_time,
        notes=appointment_data.notes
    )
    return created_appointment


@appointments_router.get("/", response_model=List[AppointmentResponseSchema])
async def get_all_appointments_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return per page."),
    include_deleted: bool = Query(False, description="Set to true to include soft-deleted appointment records."),
    patient_id: Optional[UUID] = Query(None, description="Filter appointments by patient ID."),
    doctor_id: Optional[UUID] = Query(None, description="Filter appointments by doctor ID."),
    status_filter: Optional[AppointmentStatusEnum] = Query(None, alias="status", description="Filter appointments by status (e.g., Scheduled, Completed)."),
    start_date: Optional[datetime] = Query(None, description="Filter appointments from this start date/time (ISO format, UTC recommended)."),
    end_date: Optional[datetime] = Query(None, description="Filter appointments up to this end date/time (ISO format, UTC recommended)."),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Retrieve a list of appointments with various filtering options and pagination.
    """
    appointments: List[AppointmentModel] = [] 
    
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
    
    if limit is not None:
        return appointments[skip : skip + limit]
    return appointments[skip:]


@appointments_router.get("/{appointment_id}", response_model=AppointmentResponseSchema)
async def get_appointment_by_id_route(
    appointment_id: UUID, 
    include_deleted: bool = Query(False, description="Set to true to retrieve a soft-deleted appointment."),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Retrieve a specific appointment by ID.
    """
    appointment = appointment_service.get_appointment_by_id(appointment_id, include_deleted=include_deleted) 
    if not appointment: 
        # Service returns None if not found based on include_deleted criteria.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment with ID {appointment_id} not found.")
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
    update_data_dict = appointment_update_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    updated_appointment: Optional[AppointmentModel] = None 
    
    new_status = update_data_dict.pop("status", None)
    notes_for_update = update_data_dict.pop("notes", None) 
    if notes_for_update is None and appointment_update_data.notes is not None: 
        notes_for_update = appointment_update_data.notes

    if update_data_dict: 
        if notes_for_update is not None and new_status is None : 
            update_data_dict['notes'] = notes_for_update
        updated_appointment = appointment_service.update_appointment_details(appointment_id, update_data_dict)
        # update_appointment_details in service raises if not found or conflict

    if new_status:
        current_notes_for_status = appointment_update_data.notes 
        updated_appointment_after_status_change = appointment_service.change_appointment_status(
            appointment_id, 
            new_status, 
            current_notes_for_status
        )
        # change_appointment_status in service raises if not found
        updated_appointment = updated_appointment_after_status_change
    
    if not updated_appointment:
        logger_appointments.warning(f"Update for appointment {appointment_id} resulted in no effective change, re-fetching current state.")
        updated_appointment = appointment_service.get_appointment_by_id(appointment_id, include_deleted=True) # Fetch current state
        if not updated_appointment: # Should be caught by service exceptions if it's truly not found
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Appointment with ID {appointment_id} not found.")

    return updated_appointment


@appointments_router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_appointment(
    appointment_id: UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Soft delete an appointment.
    """
    appointment_service.soft_delete_appointment(appointment_id)
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
    return restored_appointment