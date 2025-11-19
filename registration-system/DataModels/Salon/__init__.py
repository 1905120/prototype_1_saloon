"""
DataModels package for Salon Prototype 2
Contains all data model definitions and schemas
"""

from .data_models import (
    Customer,
    Client,
    Appointment,
    BookingConfirmation,
    GetFieldMapping,
    CUSTOMER_SCHEMA,
    CLIENT_SCHEMA,
    APPOINTMENT_SCHEMA,
    RESERVATION_SCHEMA
)

__all__ = [
    'Customer',
    'Client',
    'Appointment',
    'BookingConfirmation',
    'GetFieldMapping',
    'CUSTOMER_SCHEMA',
    'CLIENT_SCHEMA',
    'APPOINTMENT_SCHEMA',
    'RESERVATION_SCHEMA'
]
