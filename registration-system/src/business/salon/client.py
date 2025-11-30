"""
Client business logic for salon operations
"""
from typing import Dict, Any
import logging
import json
import os
logger = logging.getLogger(__name__)
from src.core.BusinessServiceManagement import business_service_cache

class Client:
    """Client business logic handler"""
    def write_record(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)

            return True
        except Exception as e:
            logger.error(f'Err while write disk write : {str(e)}')
            return False

    def update_service_business_map(self, SALON_SERVICE_BUSINESS_MAP_DATA_PATH, session_cache, all_Services):
        
        try:    

            

            #update service business map
            services       = session_cache.services
            location_data  = session_cache.location
            salon_name     = session_cache.salonName
            adderess       = session_cache.salonAddress
            client_id      = session_cache.id

            serviceBusinessMap = {}
            if os.path.exists(SALON_SERVICE_BUSINESS_MAP_DATA_PATH):
                with open(SALON_SERVICE_BUSINESS_MAP_DATA_PATH, 'r') as f:
                    serviceBusinessMap = json.load(f)
            if "salon" not in serviceBusinessMap:
                serviceBusinessMap["salon"] = {}

        except Exception as e:
            logger.error(str(e))
            serviceBusinessMap = {}

        for service_id, each_service in all_Services.items():
                if service_id not in serviceBusinessMap["salon"]:
                    serviceBusinessMap["salon"][service_id] = {}
                if client_id not in serviceBusinessMap["salon"][service_id]:
                    serviceBusinessMap["salon"][service_id][client_id] = {}
                if location_data:
                    serviceBusinessMap["salon"][service_id][client_id]["location"] = location_data
                if adderess:
                    serviceBusinessMap["salon"][service_id][client_id]["address"] = adderess
                if salon_name:
                    serviceBusinessMap["salon"][service_id][client_id]["salonName"] = salon_name
                serviceBusinessMap["salon"][service_id][client_id]["serviceName"] = each_service
        return serviceBusinessMap
    
    async def create(self, session_cache, current_version_data, field_validation_error) -> Dict[str, Any]:
        """Create new client"""
        try:
            if hasattr(session_cache, 'session_id') :
                session_id = session_cache.session_id
            else :
                raise Exception("Session Id Missing")

            # from src.common.constants import REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER
            # field_validation_error["missing_keys"] = [key for key in field_validation_error["missing_keys"] if key in REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER]
            # if field_validation_error["missing_keys"]:
            #     missing_fields = [f'missing field :- {each_field}' for each_field in field_validation_error["missing_keys"]]
            #     raise Exception("; ".join(missing_fields))

            from src.common.constants import SALON_BUSINESS_CLIENT_LIVE_DATA_PATH, SALON_SERVICE_BUSINESS_MAP_DATA_PATH

            # Atomic write
            all_Services = {}
            for each_service in current_version_data["services"]:
                service_id = business_service_cache.get_operation_id(session_cache.business, each_service)
                all_Services[service_id] = each_service
            current_version_data["services"] = all_Services

            current_record_path     = f"{SALON_BUSINESS_CLIENT_LIVE_DATA_PATH}/{session_cache.entity_id}.json"

            self.write_record(current_record_path, current_version_data)

            serviceBusinessMap = self.update_service_business_map(SALON_SERVICE_BUSINESS_MAP_DATA_PATH, session_cache, all_Services)            

            self.write_record(SALON_SERVICE_BUSINESS_MAP_DATA_PATH, serviceBusinessMap)

            return {
                        "result"  : {
                                        "response" : {
                                            "session_id"                : getattr(session_cache, "session_id", None),
                                            "client  _id"               : getattr(session_cache, "phone", None),
                                            "session_record_id"         : getattr(session_cache, "entity_id", None),
                                            "isRecordStored"            : True
                                                    },
                                    "status": "SUCCESS",
                                    "message": "action {0} successfully".format(getattr(session_cache, "action", None))
                                    },
                     "err_details" : {}
                    }
        except Exception as e:
                return {"result"  : {
                                    "response" : {
                                                    "session_id"                : getattr(session_cache, "session_id", None),
                                                    "customer_id"               : getattr(session_cache, "phone", None),
                                                    "session_record_id"         : getattr(session_cache, "entity_id", None),
                                                    "isRecordStored"            : False
                                                },
                                    "status"  : "FAILED",
                                    "message" : "action {0} failed due to err {1}".format(getattr(session_cache, "action", None), str(e))
                                    },
                    "err_details" : {
                                        "err_msg" : str(e),
                                        "err_type": "BUSSINESS-PROCESS-ERR"
                                    }
                    }
    
    async def update(self, session_cache, current_version_data, field_validation_error) -> Dict[str, Any]:
        try:
            if hasattr(session_cache, 'session_id') :
                session_id = session_cache.session_id
            else :
                raise Exception("Session Id Missing")

            # from src.common.constants import REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER
            # field_validation_error["missing_keys"] = [key for key in field_validation_error["missing_keys"] if key in REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER]
            # if field_validation_error["missing_keys"]:
            #     missing_fields = [f'missing field :- {each_field}' for each_field in field_validation_error["missing_keys"]]
            #     raise Exception("; ".join(missing_fields))

            from src.common.constants import SALON_BUSINESS_CLIENT_LIVE_DATA_PATH, SALON_SERVICE_BUSINESS_MAP_DATA_PATH

            # Atomic write
            all_Services = {}
            for each_service in current_version_data["services"]:
                service_id = business_service_cache.get_operation_id(session_cache.business, each_service)
                all_Services[service_id] = each_service
            current_version_data["services"] = all_Services

            current_record_path     = f"{SALON_BUSINESS_CLIENT_LIVE_DATA_PATH}/{session_cache.entity_id}.json"

            self.write_record(current_record_path, current_version_data)

            serviceBusinessMap = self.update_service_business_map(SALON_SERVICE_BUSINESS_MAP_DATA_PATH, session_cache, all_Services)            

            self.write_record(SALON_SERVICE_BUSINESS_MAP_DATA_PATH, serviceBusinessMap)

            return {
                        "result"  : {
                                        "response" : {
                                            "session_id"                : getattr(session_cache, "session_id", None),
                                            "client  _id"               : getattr(session_cache, "phone", None),
                                            "session_record_id"         : getattr(session_cache, "entity_id", None),
                                            "isRecordStored"            : True
                                                    },
                                    "status": "SUCCESS",
                                    "message": "action {0} successfully".format(getattr(session_cache, "action", None))
                                    },
                     "err_details" : {}
                    }
        except Exception as e:
                return {"result"  : {
                                    "response" : {
                                                    "session_id"                : getattr(session_cache, "session_id", None),
                                                    "customer_id"               : getattr(session_cache, "phone", None),
                                                    "session_record_id"         : getattr(session_cache, "entity_id", None),
                                                    "isRecordStored"            : False
                                                },
                                    "status"  : "FAILED",
                                    "message" : "action {0} failed due to err {1}".format(getattr(session_cache, "action", None), str(e))
                                    },
                    "err_details" : {
                                        "err_msg" : str(e),
                                        "err_type": "BUSSINESS-PROCESS-ERR"
                                    }
                    }
    
    async def delete(self, payload: Dict[str, Any], cache_data: Dict[str, Any], entity_id: str, seq_id: int) -> Dict[str, Any]:
        """Delete client (soft delete)"""
        try:
            logger.info(f"Deleting client with entity_id: {entity_id}, seq_id: {seq_id}")
            
            client_key = payload.phone
            if client_key not in cache_data:
                return {
                    "status": "FAILED",
                    "error": f"Client not found: {client_key}",
                    "message": "Client does not exist"
                }
            
            client = cache_data[client_key]
            client["deleted"] = True
            client["deleted_at"] = __import__('datetime').datetime.now().isoformat()
            client["seq_id"] = seq_id
            
            return {
                "status": "SUCCESS",
                "entity_id": entity_id,
                "seq_id": seq_id,
                "message": "Client deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting client: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "message": "Failed to delete client"
            }
