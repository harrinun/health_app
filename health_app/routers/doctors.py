from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from health_app.services.doctor_service import DoctorService
from health_app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["Doctors"])

def get_doctor_service():
    return DoctorService()

@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(data: DoctorCreate, service: DoctorService = Depends(get_doctor_service)):
    try:
        return service.create_doctor(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DoctorOut])
def list_doctors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: DoctorService = Depends(get_doctor_service)
):
    return service.list_doctors(page=page, page_size=page_size)

@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, service: DoctorService = Depends(get_doctor_service)):
    doctor = service.get_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: str, data: DoctorUpdate, service: DoctorService = Depends(get_doctor_service)):
    doctor = service.update_doctor(doctor_id, data)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or already deleted")
    return doctor

@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor(doctor_id: str, service: DoctorService = Depends(get_doctor_service)):
    success = service.delete_doctor(doctor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Doctor not found or already deleted")
