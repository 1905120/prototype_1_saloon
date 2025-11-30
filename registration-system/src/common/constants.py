"""
Application constants
"""

# Worker configuration
MAX_WORKER_THREADS = 5
QUEUE_TIMEOUT = 1  # seconds
QUEUE_MAX_SIZE = 0  # 0 = unlimited

B_SALON_META_SCHEMA_PATH       = "DataModels/Salon/salon_meta.json"
B_SALON_CUST_META_SCHEMA_PATH  = "DataModels/Salon/CustomerSchema/Schema/meta-data.json"
B_SALON_CLIENT_META_SCHEM_PATH = "DataModels/Salon/ClientSchema/Schema/meta-data.json"
B_SALON_CUST_CREATE_SCHEM_PATH = "DataModels/Salon/CustomerSchema/Schema/create_schema.json"
B_SALON_CUST_UPDATE_SCHEM_PATH = "DataModels/Salon/CustomerSchema/Schema/update_schema.json"
B_SALON_CLIENT_CREATE_SCHEM_PATH = "DataModels/Salon/ClientSchema/Schema/create_schema.json"

B_SALON_META_DATA_PATH         = "data/businesses/salon/meta_data/business_meta_data.json"
B_SALON_CUST_META_DATA_PATH    = "data/businesses/salon/meta_data/customer_meta_data.json"
B_SALON_CLIENT_META_DATA_PATH  = "data/businesses/salon/meta_data/client_meta_data.json"


BUSINESS_SERVICE_MODEL_SCHEMA_PATH = "DataModels/BusinessServiceModel/business_service_model.json"
BUSINESS_SERVICE_MODEL_DATA_PATH   = "data/business_service_model"
BUSINESS_SERVICE_MODEL_FILE_PATH   = "data/business_service_model/business_service.json"

SALON_BUSINESS_CUSTOMER_LIVE_DATA_PATH = "data/businesses/salon/Customer/live"
SALON_BUSINESS_CLIENT_LIVE_DATA_PATH = "data/businesses/salon/Client/live"
SALON_BUSINESS_CUSTOMER_HISTORY_DATA_PATH = "data/businesses/salon/history"
SALON_BUSINESS_CUSTOMER_BOOKING_MAP_PATH = "data/businesses/salon/customer_booking_map"
SALON_BUSINESS_CUSTOMER_BOOKING_MAP_SCHEMA_PATH = "DataModels/Salon/CustomerBookingMapSchema/customer_booking_map.json"
SALON_SERVICE_BUSINESS_MAP_SCHEMA_PATH = "DataModels/Salon/service_business_map/service_business_map.json"
SALON_SERVICE_BUSINESS_MAP_DATA_PATH = "data/businesses/salon/ServiceBusinessMap/Service_Business_Map.json"
SALON_BUSINESS_SYSTEM_ACTIONS = ["get-customer_booking_map"]
REQUIRED_MAND_FIELD_FOR_SALON_CUSTOMER = ["name", "phone", "business", "service_type"]

TEST = True

# Lock configuration
ENABLE_LOCKING = True  # Set to True to enable locking, False for lock-free reads

# System Cache configuration
SYSTEM_CACHE_PATH = "data/system_cache/system_cache.json"

# System Cache Manager singleton instance
def _get_system_cache_manager():
    """Lazy load system cache manager to avoid circular imports"""
    from src.system_cache.manager import get_system_cache_manager
    return get_system_cache_manager(SYSTEM_CACHE_PATH)

# Export as a callable that returns the singleton
system_cache = _get_system_cache_manager

SUGGETION_OF_SALONS_DEFAULT = 5 #KM radius