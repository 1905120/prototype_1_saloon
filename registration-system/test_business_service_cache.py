"""
Test file for BusinessServiceCache
"""
import logging
from src.core.BusinessServiceManagement import business_service_cache
from src.common.constants import BUSINESS_SERVICE_MODEL_SCHEMA_PATH, BUSINESS_SERVICE_MODEL_DATA_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting BusinessServiceCache test...")
    logger.info(f"Schema path: {BUSINESS_SERVICE_MODEL_SCHEMA_PATH}")
    logger.info(f"Data path: {BUSINESS_SERVICE_MODEL_DATA_PATH}")
    
    # Test 1: Get business service model (file is business_service.json, contains salon)
    logger.info("\n=== Test 1: Get business service model ===")
    business_service = business_service_cache.get_business_service("business_service")
    logger.info(f"Business service model: {business_service}")
    
    # Test 2: Get all businesses
    logger.info("\n=== Test 2: Get all businesses ===")
    all_businesses = business_service_cache.get_all_businesses()
    logger.info(f"All businesses: {all_businesses}")
    
    # Test 3: Get operation ID for hair-cutting service (business_service contains salon)
    logger.info("\n=== Test 3: Get operation ID for hair-cutting service ===")
    operation_id = business_service_cache.get_operation_id_by_service("business_service", "hair-cutting")
    logger.info(f"Operation ID for hair-cutting: {operation_id}")
    
    # Test 4: Get operation ID for manicure service
    logger.info("\n=== Test 4: Get operation ID for manicure service ===")
    operation_id_2 = business_service_cache.get_operation_id_by_service("business_service", "manicure")
    logger.info(f"Operation ID for manicure: {operation_id_2}")
    
    # Test 5: Get business service again (should use cache)
    logger.info("\n=== Test 5: Get business service again (cached) ===")
    business_service_cached = business_service_cache.get_business_service("business_service")
    logger.info(f"Business service (cached): {business_service_cached}")
    
    logger.info("\n=== Test completed ===")
