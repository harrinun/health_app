from fastapi import FastAPI
from health_app.routers import patients, doctors, appointments, medical_records
from health_app.middleware.log_request_time import LogRequestTimeMiddleware
from health_app.utils.exceptions import register_exception_handlers

app = FastAPI(title="Patient Medical Record Management System")


app.add_middleware(LogRequestTimeMiddleware)
register_exception_handlers(app)

app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(medical_records.router)



@app.get("/")
def root():
    return {"message": "Welcome to the Patient Medical Record Management System API"}