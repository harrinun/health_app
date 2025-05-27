from fastapi import HTTPException, status

class BaseCustomException(HTTPException):
    """Base class for custom exceptions in this application."""
    def __init__(self, status_code: int, detail: str = None, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class ResourceNotFoundException(BaseCustomException):
    """Custom exception for a resource not being found."""
    def __init__(self, resource_name: str, resource_id: any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} with ID '{str(resource_id)}' not found." # Ensure resource_id is stringified
        )

class InvalidOperationException(BaseCustomException):
    """Custom exception for an invalid operation attempt."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class DoctorUnavailableException(BaseCustomException):
    """Custom exception for when a doctor is unavailable for an appointment."""
    def __init__(self, doctor_id: any, appointment_time: any, reason: str = "already booked"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT, # 409 Conflict is often used for this
            detail=f"Doctor with ID '{str(doctor_id)}' is unavailable at {str(appointment_time)} because they are {reason}."
        )

class ConcurrencyException(BaseCustomException):
    """Custom exception for concurrency issues, e.g., folder number generation clash."""
    def __init__(self, detail: str = "A concurrency conflict occurred. Please try again."):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

# Example of a more specific validation-related error if needed beyond Pydantic's
# class BusinessValidationException(BaseCustomException):
#     def __init__(self, detail: str):
#         super().__init__(
#             status_code=status.HTTP_400_BAD_REQUEST, # Or 422 if it's more like unprocessable entity
#             detail=detail
#         )

# You can add more specific exceptions as your application grows, for example:
# class PatientInactiveException(InvalidOperationException):
#     def __init__(self, patient_id: any):
#         super().__init__(detail=f"Operation failed: Patient with ID '{str(patient_id)}' is inactive.")

