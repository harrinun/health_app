from fastapi import APIRouter, HTTPException, Depends, status, Query 
from typing import List, Optional 
from uuid import UUID 
from datetime import date 
import logging 

# Schemas
from ..schemas.medical_record_schema import (
    MedicalRecordCreateSchema,
    MedicalRecordUpdateSchema,
    MedicalRecordResponseSchema
)
# Services
from ..services.medical_record_service import MedicalRecordService
# Repositories for service dependencies
from ..repository.medical_record_repository import MedicalRecordRepository
from ..repository.patient_repository import PatientRepository as RecordPatientRepo 
from ..repository.doctor_repository import DoctorRepository as RecordDoctorRepo   
from ..repository.appointment_repository import AppointmentRepository as RecordApptRepo 
# Import the model for type hinting
from ..models.medical_record_model import MedicalRecordModel # Added for type hint

logger_medical_records = logging.getLogger("health_app.routers.medical_records_router") 

# --- Router Setup ---
medical_records_router = APIRouter( 
    prefix="/medical-records", 
    tags=["Medical Records"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Medical record not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input or operation for medical record"},
        status.HTTP_409_CONFLICT: {"description": "Conflict error related to medical record resource"}
    }
)

# --- Dependency for MedicalRecordService ---
_record_repository_instance = MedicalRecordRepository()
_record_patient_repo_instance = RecordPatientRepo()
_record_doctor_repo_instance = RecordDoctorRepo() 
_record_appt_repo_instance = RecordApptRepo()     


def get_medical_record_service() -> MedicalRecordService:
    return MedicalRecordService(
        medical_record_repository=_record_repository_instance,
        patient_repository=_record_patient_repo_instance,
        doctor_repository=_record_doctor_repo_instance, 
        appointment_repository=_record_appt_repo_instance 
    )

# --- Path Operations ---

@medical_records_router.post("/", response_model=MedicalRecordResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_new_medical_record(
    record_data: MedicalRecordCreateSchema,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Create a new medical record for a patient.
    """
    created_record = record_service.create_medical_record(
        patient_id=record_data.patient_id,
        diagnosis=record_data.diagnosis,
        prescriptions=record_data.prescriptions,
        treatment_date=record_data.treatment_date,
        doctor_notes=record_data.doctor_notes,
        attending_doctor_id=record_data.attending_doctor_id,
        appointment_id=record_data.appointment_id
    )
    return created_record

@medical_records_router.get("/", response_model=List[MedicalRecordResponseSchema])
async def get_all_medical_records_list(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return per page."),
    include_deleted: bool = Query(False, description="Set to true to include soft-deleted medical records."),
    patient_id: Optional[UUID] = Query(None, description="Filter medical records by patient ID."),
    attending_doctor_id: Optional[UUID] = Query(None, description="Filter medical records by attending doctor ID."),
    treatment_date_filter: Optional[date] = Query(None, alias="treatment_date", description="Filter medical records by treatment date (YYYY-MM-DD)."),
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Retrieve a list of medical records with filtering and pagination.
    """
    records: List[MedicalRecordModel] = [] 
    
    if patient_id:
        records = record_service.get_medical_records_for_patient(patient_id, include_deleted)
    elif attending_doctor_id:
        records = record_service.get_medical_records_by_attending_doctor(attending_doctor_id, include_deleted)
    elif treatment_date_filter:
        records = record_service.get_medical_records_by_treatment_date(treatment_date_filter, include_deleted)
    else:
        records = record_service.get_all_medical_records(skip=skip, limit=limit, include_deleted=include_deleted)
        return records 

    if limit is not None:
        return records[skip : skip + limit]
    return records[skip:]


@medical_records_router.get("/{record_id}", response_model=MedicalRecordResponseSchema)
async def get_medical_record_by_id_route(
    record_id: UUID,
    include_deleted: bool = Query(False, description="Set to true to retrieve a soft-deleted medical record."),
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Retrieve a specific medical record by ID.
    """
    record = record_service.get_medical_record_by_id(record_id, include_deleted=include_deleted) 
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medical record with ID {record_id} not found.")
    return record

@medical_records_router.put("/{record_id}", response_model=MedicalRecordResponseSchema)
async def update_existing_medical_record(
    record_id: UUID,
    record_update_data: MedicalRecordUpdateSchema,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Update an existing medical record.
    """
    update_data_dict = record_update_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    updated_record = record_service.update_medical_record(record_id, update_data_dict)
    if not updated_record: # Service raises if not found or invalid operation
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Medical record with ID {record_id} not found or could not be updated (e.g., inactive).")
    return updated_record

@medical_records_router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_medical_record(
    record_id: UUID,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Soft delete a medical record.
    """
    record_service.soft_delete_medical_record(record_id) # Service raises if not found
    return None

@medical_records_router.put("/{record_id}/restore", response_model=MedicalRecordResponseSchema)
async def restore_deleted_medical_record(
    record_id: UUID,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Restore a soft-deleted medical record.
    """
    restored_record = record_service.restore_medical_record(record_id) # Service raises if not found/not deleted
    return restored_record