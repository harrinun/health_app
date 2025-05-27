from fastapi import APIRouter, HTTPException, Depends, status, Query # Re-import for clarity
from pathlib import Path # Re-import for clarity
from typing import List, Optional # Re-import for clarity
from uuid import UUID # Re-import for clarity
from datetime import date # Re-import for clarity

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


# --- Router Setup ---
medical_records_router = APIRouter( # Renamed APIRouter instance
    prefix="/medical-records", 
    tags=["Medical Records"],
    responses={404: {"description": "Medical record not found"}}
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
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating medical record.")

@medical_records_router.get("/", response_model=List[MedicalRecordResponseSchema])
async def get_all_medical_records_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_deleted: bool = Query(False),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient ID"),
    attending_doctor_id: Optional[UUID] = Query(None, description="Filter by attending doctor ID"),
    treatment_date_filter: Optional[date] = Query(None, alias="treatment_date", description="Filter by treatment date (YYYY-MM-DD)"), # Changed alias
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Retrieve a list of medical records with filtering and pagination.
    """
    if patient_id:
        records = record_service.get_medical_records_for_patient(patient_id, include_deleted)
    elif attending_doctor_id:
        records = record_service.get_medical_records_by_attending_doctor(attending_doctor_id, include_deleted)
    elif treatment_date_filter:
        records = record_service.get_medical_records_by_treatment_date(treatment_date_filter, include_deleted)
    else:
        records = record_service.get_all_medical_records(skip=skip, limit=limit, include_deleted=include_deleted)
        return records 

    # Manual pagination for filtered results
    if limit:
        return records[skip : skip + limit]
    return records[skip:]


@medical_records_router.get("/{record_id}", response_model=MedicalRecordResponseSchema)
async def get_medical_record_by_id_route(
    record_id: UUID,
    record_service: MedicalRecordService = Depends(get_medical_record_service),
    include_deleted: bool = Query(False, description="Whether to include soft-deleted record") # Allow fetching soft-deleted if specified
):
    """
    Retrieve a specific medical record by ID.
    """
    record = record_service.get_medical_record_by_id(record_id) # Service get_by_id should handle include_deleted if needed
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found.")
    if record.date_deleted is not None and not include_deleted: # Check if active
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record is inactive.")
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
    try:
        update_data_dict = record_update_data.model_dump(exclude_unset=True)
        if not update_data_dict:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
        
        updated_record = record_service.update_medical_record(record_id, update_data_dict)
        if not updated_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found or could not be updated.")
        return updated_record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating medical record.")

@medical_records_router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_existing_medical_record(
    record_id: UUID,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Soft delete a medical record.
    """
    deleted_record = record_service.soft_delete_medical_record(record_id)
    if not deleted_record:
        existing = record_service.get_medical_record_by_id(record_id=record_id, include_deleted=True)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found.")
    return None

@medical_records_router.put("/{record_id}/restore", response_model=MedicalRecordResponseSchema)
async def restore_deleted_medical_record(
    record_id: UUID,
    record_service: MedicalRecordService = Depends(get_medical_record_service)
):
    """
    Restore a soft-deleted medical record.
    """
    restored_record = record_service.restore_medical_record(record_id)
    if not restored_record:
        existing = record_service.get_medical_record_by_id(record_id=record_id, include_deleted=True)
        if not existing:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found.")
        if existing.date_deleted is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medical record is not deleted.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not restore medical record.")
    return restored_record

