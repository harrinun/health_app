"""
Base SQLAlchemy models and mixins for the health management system.
These models represent the database schema and work alongside Pydantic models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Date, Text
from sqlalchemy.ext.declarative import declared_attr

from ..config import Base


class TimestampMixin:
    """
    Mixin that adds timestamp columns to SQLAlchemy models.
    Provides created, updated, and soft-delete functionality.
    """
    
    @declared_attr
    def date_created(cls):
        """Timestamp when the record was created (UTC)"""
        return Column(
            DateTime(timezone=True), 
            nullable=False, 
            default=lambda: datetime.now(timezone.utc),
            comment="Timestamp when the record was created (UTC)"
        )
    
    @declared_attr 
    def date_updated(cls):
        """Timestamp when the record was last updated (UTC)"""
        return Column(
            DateTime(timezone=True), 
            nullable=False, 
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            comment="Timestamp when the record was last updated (UTC)"
        )
    
    @declared_attr
    def date_deleted(cls):
        """Timestamp when the record was soft-deleted (UTC). NULL if not deleted"""
        return Column(
            DateTime(timezone=True), 
            nullable=True, 
            default=None,
            comment="Timestamp when the record was soft-deleted (UTC). NULL if not deleted"
        )


class BiodataColumns:
    """
    Mixin that adds biodata columns to SQLAlchemy models.
    Contains personal identification information.
    """
    
    @declared_attr
    def first_name(cls):
        """Person's first name"""
        return Column(
            String(100), 
            nullable=False,
            comment="Person's first name"
        )
    
    @declared_attr
    def last_name(cls):
        """Person's last name"""
        return Column(
            String(100), 
            nullable=False,
            comment="Person's last name"
        )
    
    @declared_attr
    def date_of_birth(cls):
        """Person's date of birth"""
        return Column(
            Date, 
            nullable=False,
            comment="Person's date of birth"
        )
    
    @declared_attr
    def gender(cls):
        """Person's gender"""
        return Column(
            String(20), 
            nullable=False,
            comment="Person's gender"
        )


class ContactInformationColumns:
    """
    Mixin that adds contact information columns to SQLAlchemy models.
    Contains phone, email, and address information.
    """
    
    @declared_attr
    def phone_number(cls):
        """Primary phone number"""
        return Column(
            String(20), 
            nullable=False,
            comment="Primary phone number"
        )
    
    @declared_attr
    def email(cls):
        """Email address (optional)"""
        return Column(
            String(255), 
            nullable=True,
            comment="Email address (optional)"
        )
    
    @declared_attr
    def address(cls):
        """Physical address"""
        return Column(
            Text, 
            nullable=False,
            comment="Physical address"
        )


class EmergencyContactColumns:
    """
    Mixin that adds emergency contact columns to SQLAlchemy models.
    Contains emergency contact information.
    """
    
    @declared_attr
    def emergency_full_name(cls):
        """Full name of emergency contact"""
        return Column(
            String(200), 
            nullable=False,
            comment="Full name of emergency contact"
        )
    
    @declared_attr
    def emergency_relationship(cls):
        """Relationship to the person (e.g., Spouse, Parent)"""
        return Column(
            String(50), 
            nullable=False,
            comment="Relationship to the person (e.g., Spouse, Parent)"
        )
    
    @declared_attr
    def emergency_phone_number(cls):
        """Emergency contact's phone number"""
        return Column(
            String(20), 
            nullable=False,
            comment="Emergency contact's phone number"
        )