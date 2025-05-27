from enum import Enum

class GenderEnum(str, Enum):
    """
    Enumeration for gender.
    Using str as a mixin allows the enum members to be directly usable as strings,
    which is helpful for JSON serialization and API interactions.
    """
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    PREFER_NOT_TO_SAY = "Prefer not to say"

class AppointmentStatusEnum(str, Enum):
    """
    Enumeration for appointment statuses.
    """
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    PENDING = "Pending" # Added for appointments that are requested but not yet confirmed