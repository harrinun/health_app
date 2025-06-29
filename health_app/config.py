"""
Centralized Application Configuration using Pydantic Settings.

This module loads settings from environment variables and a .env file.
It provides a single configuration object for use throughout the application.
"""
import os
from pydantic_settings import BaseSettings
from typing import Literal

# Determine the project's base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    """
    Defines application settings and reading from environment variables.
    """
    # Application Settings
    APP_NAME: str = "Patient Medical Record Management System"
    API_V1_STR: str = "/api/v1"
    
    # Persistence Layer Configuration to switch between 'json' and 'database'
    PERSISTENCE_MODE: Literal["database", "json"] = "database"  # Default to 'database'

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:port_number/db_name"
    SQL_ECHO: bool = False

    # Email Configuration
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM_NAME: str = "Health App"
    
    class Config:
        # Specifies the .env file to load
        env_file = os.path.join(os.path.dirname(BASE_DIR), ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Create a single, importable instance of the settings
settings = Settings()

