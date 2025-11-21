"""
DataPipeline class - main orchestrator
Load → Validate → Process → Persist
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from src.common.enums import OperationType, PipelineStatus
from src.core.session import SessionManager
from src.core.universal_cache import UniversalCache
from src.errors.error_handler import ErrorHandler
import os
import json
import logging 

logger = logging.getLogger(__name__)

class DataPipeline:
    """
    Main pipeline orchestrator
    Handles: Load → Validate → Process → Persist
    """
    
    def __init__(self, session_cache):
        """
        Initialize pipeline
        
        Args:
            universal_cache: UniversalCache instance
        """
        self.session_cache = session_cache
        self.DEFAULT_CUSTOMER_SCHEMA = {
                                        "id": "",
                                        "name": "",
                                        "email": "",
                                        "phone": "",
                                        "dateOfBirth": "",
                                        "address": "",
                                        "location": "",
                                        "version": "",
                                        "action": "",
                                        "approvalStatus":"",
                                        "updatedAt": "",
                                        "updatedFields": "",
                                        "registeredAt": "",
                                        "business": "",
                                        "service_type": "",
                                        "operation_id": ""
                                    }


    def _get_default_value(self, prop_schema: Dict[str, Any]) -> Any:
        """
        Get default value based on property schema type
        
        Args:
            prop_schema: Property schema definition
        
        Returns:
            Default value for the property type
        """
        prop_type = prop_schema.get("type")
        
        if prop_type == "object":
            if "properties" in prop_schema:
                obj = {}
                for key, value_schema in prop_schema["properties"].items():
                    obj[key] = _get_default_value(value_schema)
                return obj
            return {}
        
        elif prop_type == "array":
            return []
        
        elif prop_type == "string":
            if prop_schema.get("format") == "date-time":
                return datetime.now().isoformat()
            return ""
        
        elif prop_type == "integer":
            return 0
        
        elif prop_type == "number":
            return 0.0
        
        elif prop_type == "boolean":
            return False
        
        else:
            return None

    def create_default_schema_from_file(self) -> Dict[str, Any]:
        """
        Create default schema structure from a JSON schema file
        
        Args:
            schema_file_path: Path to JSON schema file
        
        Returns:
            Default schema structure
        
        Raises:
            FileNotFoundError: If schema file not found
            json.JSONDecodeError: If schema file is invalid JSON
        """
        try:

            schema_file_path = f"DataModels/{self.session_cache.business}/CustomerSchema/Schema/create_schema.json"
            
            if not os.path.exists(schema_file_path):
                logger.warning(f"Schema file not found: {schema_file_path}, using default")
                return DEFAULT_CUSTOMER_SCHEMA.copy()
            
            with open(schema_file_path, 'r') as f:
                schema = json.load(f)
            
            # Build default structure from schema
            default_data = {}
            
            if "properties" in schema:
                for prop_name, prop_schema in schema["properties"].items():
                    default_data[prop_name] = self._get_default_value(prop_schema)
            
            logger.info(f"Created default schema from file: {schema_file_path}")
            return default_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {str(e)}")
            return self.DEFAULT_CUSTOMER_SCHEMA.copy()
        except Exception as e:
            logger.error(f"Error loading schema file: {str(e)}")
            return self.DEFAULT_CUSTOMER_SCHEMA.copy()
    
    # ============ PHASE 1: LOAD ============

    def load(self):
        """
        Load phase: Read latest version record from path and create current version data
        
        Args:
            path: Path to the record file to load
        
        Returns:
            Dictionary containing:
                - latest_version: Latest version number from loaded data
                - current_version_data: Current version data created from latest version record merged with session cache attributes
        """
        import json
        import logging
        from src.common.constants import SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH
        logger = logging.getLogger(__name__)
        
        try:

            latest_version_record = {}
            current_version_data = {}

            live_data_store_path = f'{SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH}/{self.session_cache.latest_version_record_id}'
            
            if os.path.exists(live_data_store_path):
                with open(live_data_store_path, 'r') as f:
                    latest_version_record = dict(json.load(f))
            # else:
            #     logger.error(f'Err on loadin {self.session_cache.latest_version_record_id} record from {SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH}')
            #     ErrorHandler.raise_datapipeline_error(f'Err on loadin {self.session_cache.latest_version_record_id} record from {SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH}')
            #     return None, current_version_data

            # Create current version data from latest version record
            current_version_data = latest_version_record.copy() if latest_version_record else {}
            
            empty_schema = self.create_default_schema_from_file()

            # Merge session cache attributes into current version data
            if self.session_cache:
                # Check each attribute in session_cache
                for key, value in self.session_cache.__dict__.items():
                    # Add session cache attribute to current version data
                    if key == 'operation' or key not in empty_schema:
                        continue
                    current_version_data[key] = value
            
            # result = {
            #     'latest_version': latest_version,
            #     'current_version_data': current_version_data
            # }
            
            # logger.info(f"Load phase completed - Latest version: {latest_version}, Current version data keys: {list(current_version_data.keys())}")
            return current_version_data, empty_schema
            
        except FileNotFoundError:
            logger.error(f"Record file not found at {path}")
            ErrorHandler.raise_processing_error(f"Record not found at {path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in record file at {path}")
            ErrorHandler.raise_processing_error(f"Invalid JSON format at {path}")
        except Exception as e:
            logger.error(f"Error loading record from {path}: {str(e)}")
            ErrorHandler.raise_processing_error(f"Load phase failed: {str(e)}") 
    
    # ============ PHASE 2: VALIDATE ============
    def field_validate(self, current_version_data, empty_schema):

        action = getattr(self.session_cache, "action", None)
        missing_fields = []
        field_validation_error = {}
        if action == "create" or action == "create-customer":
            field_validation_error["missing_keys"]    = [each_field for each_field in empty_schema if each_field not in current_version_data]
            if not field_validation_error["missing_keys"]:
                field_validation_error["missing_key_values"]  = [each_field for each_field in empty_schema if not current_version_data[each_field]]
            else:
                field_validation_error["missing_key_values"] = []
        return field_validation_error
    
    # ============ TEMPLATE FLOW ============
    async def template_flow(self, function) -> Dict[str, Any]:
        """
        Template flow: Execute pipeline phases in sequence
        Calls: load → validate → process → persist
        
        Args:
            session_id: Session identifier
            validator_func: field Validation function
            business function()
            api_func: Optional API call function
        
        Returns:
            Final session with all phases completed
        """
        try:
            # Phase 1: Load
            current_version_data, empty_schema = self.load()
            
            # Phase 2: Validate
            field_validation_error = self.field_validate(current_version_data, empty_schema)
            
            response = await function(self.session_cache, current_version_data, field_validation_error)

            return response
            
        except Exception as e:
            raise
    
    def _update_final_metadata(self, session: Dict[str, Any]) -> None:
        """
        Update metadata at end of process with lock
        
        Args:
            session: Final session object
        """
        phone = session.get("phone")
        version = session.get("version")
        session_id = session.get("session_id")
        
        if phone and version and session_id:
            self.cache.acquire_write_lock()
            try:
                metadata = self.cache.read(phone)
                if metadata:
                    metadata["latest_version"] = version
                    self.cache.update(phone, metadata)
            finally:
                self.cache.release_write_lock()
