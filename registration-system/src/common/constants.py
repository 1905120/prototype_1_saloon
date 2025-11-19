"""
Application constants
"""

# Worker configuration
MAX_WORKER_THREADS = 10
QUEUE_TIMEOUT = 1  # seconds
QUEUE_MAX_SIZE = 0  # 0 = unlimited

B_SALON_META_SCHEMA_PATH       = "DataModels/Salon/salon_meta.json"
B_SALON_CUST_META_SCHEMA_PATH  = "DataModels/Salon/CustomerSchema/Schema/meta-data.json"
B_SALON_CLIENT_META_SCHEM_PATH = "DataModels/Salon/ClientSchema/Schema/meta-data.json"
B_SALON_CUST_CREATE_SCHEM_PATH = "DataModels/Salon/CustomerSchema/Schema/create_schema.json"
B_SALON_CUST_UPDATE_SCHEM_PATH = "DataModels/Salon/CustomerSchema/Schema/update_schema.json"

B_SALON_META_DATA_PATH         = "data/businesses/salon/meta_data/business_meta_data.json"
B_SALON_CUST_META_DATA_PATH    = "data/businesses/salon/meta_data/customer_meta_data.json"
B_SALON_CLIENT_META_DATA_PATH  = "data/businesses/salon/meta_data/client_meta_data.json"


BUSINESS_SERVICE_MODEL_SCHEMA_PATH = "DataModels/BusinessServiceModel/business_service_model.json"
BUSINESS_SERVICE_MODEL_DATA_PATH   = "data/business_service_model"
BUSINESS_SERVICE_MODEL_FILE_PATH   = "data/business_service_model/business_service.json"
TEST = True
