from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from health_app.services.patient_service import PatientService
from health_app.schemas.patient import PatientCreate, PatientUpdate, PatientOut

router = APIRouter(prefix="/patients", tags=["Patients"])

def get_patient_service():
    return PatientService()

@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, service: PatientService = Depends(get_patient_service)):
    try:
        return service.create_patient(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[PatientOut])
def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: PatientService = Depends(get_patient_service)
):
    return service.list_patients(page=page, page_size=page_size)

@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, service: PatientService = Depends(get_patient_service)):
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: str, data: PatientUpdate, service: PatientService = Depends(get_patient_service)):
    patient = service.update_patient(patient_id, data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or already deleted")
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, service: PatientService = Depends(get_patient_service)):
    success = service.delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found or already deleted")
