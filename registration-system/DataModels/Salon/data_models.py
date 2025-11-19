from CustomerSchema.Customer.customer import Customer
from ClientSchema.Client.client import Client
from BookingSchema.Book.slot_registration import Appointment, BookingConfirmation
from pathlib import Path

# Schema file paths
CUSTOMER_SCHEMA = f'{Path(__file__).parent}/CustomerSchema/Schema/create_schema.json'
# CUSTOMER_UPDATE_SCHEMA = "CustomerSchema/Schema/update_schema.json"
# CUSTOMER_DELETE_SCHEMA = "CustomerSchema/Schema/delete_schema.json"
# CUSTOMER_METADATA = "CustomerSchema/Schema/meta-data.json"

CLIENT_SCHEMA = f'{Path(__file__).parent}/ClientSchema/Schema/create_schema.json'
# CLIENT_UPDATE_SCHEMA = "ClientSchema/Schema/update_schema.json"
# CLIENT_DELETE_SCHEMA = "ClientSchema/Schema/delete_schema.json"
# CLIENT_METADATA = "ClientSchema/Schema/meta-data.json"

APPOINTMENT_SCHEMA = f'{Path(__file__).parent}/BookingSchema/Schema/customer_booking_schema.json'
# APPOINTMENT_UPDATE_SCHEMA = "BookingSchema/Schema/update_schema.json"
RESERVATION_SCHEMA = f'{Path(__file__).parent}/BookingSchema/Schema/client_booking_schema.json'
# BOOKING_CONFIRMATION_UPDATE_SCHEMA = "BookingSchema/Schema/update_schema.json"

__all__ = [
    'Customer',
    'Client',
    'Appointment',
    'BookingConfirmation'
]

def GetFieldMapping(class_name):
    """
    Returns a dictionary mapping field numbers to field paths for a given class.
    Reads the corresponding JSON schema and extracts all field paths.
    
    Args:
        class_name (str): One of ['Customer', 'Client', 'Appointment', 'BookingConfirmation']
    
    Returns:
        dict: Mapping of field number to field path (e.g., {1: "customerId", 2: "name", 9: "workingHours.day"})
        
    Raises:
        ValueError: If class_name is not recognized
    """
    import json
    import os
    
    # Map class names to their schema file paths
    schema_map = {
        'Customer': CUSTOMER_CREATE_SCHEMA,
        'Client': CLIENT_CREATE_SCHEMA,
        'Appointment': APPOINTMENT_SCHEMA,
        'BookingConfirmation': BOOKING_CONFIRMATION_SCHEMA
    }
    
    if class_name not in schema_map:
        raise ValueError(f"Unknown class: {class_name}. Must be one of {list(schema_map.keys())}")
    
    # Get the class object to retrieve field numbers
    class_map = {
        'Customer': Customer,
        'Client': Client,
        'Appointment': Appointment,
        'BookingConfirmation': BookingConfirmation
    }
    cls = class_map[class_name]
    if class_name == "client":
        pass
    # Build reverse mapping: field_name -> field_number
    field_number_map = {}
    for attr_name in dir(cls):
        if not attr_name.startswith('_'):
            attr_value = getattr(cls, attr_name)
            if isinstance(attr_value, int):
                field_number_map[attr_name] = attr_value
    
    # Read the schema file
    schema_path = schema_map[class_name]
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Extract field paths from schema
    field_mapping = {}
    
    def extract_fields(properties, prefix=""):
        """Recursively extract field paths from schema properties"""
        for field_name, field_def in properties.items():
            current_path = f"{prefix}.{field_name}" if prefix else field_name
            
            # Check if this field has a corresponding field number in the class
            if field_name in field_number_map:
                field_num = field_number_map[field_name]
                field_mapping[field_num] = current_path
            
            # If field has nested properties, recurse
            if isinstance(field_def, dict) and 'properties' in field_def:
                extract_fields(field_def['properties'], current_path)
            
            # Handle array items with properties
            if isinstance(field_def, dict) and 'items' in field_def:
                items = field_def['items']
                if isinstance(items, dict) and 'properties' in items:
                    extract_fields(items['properties'], current_path)
    
    # Start extraction from schema properties
    if 'properties' in schema:
        extract_fields(schema['properties'])
    
    return field_mapping
