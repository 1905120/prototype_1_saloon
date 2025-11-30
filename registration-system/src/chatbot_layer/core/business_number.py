"""
Business Number Manager - Manages WhatsApp business numbers for chatbot
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class BusinessNumberManager:
    """Manages business numbers and their configurations"""
    
    def __init__(self, config_path: str = "data/chatbot/business_numbers.json"):
        """
        Initialize business number manager
        
        Args:
            config_path: Path to business numbers configuration file
        """
        self.config_path = config_path
        self.business_numbers: Dict[str, Dict[str, Any]] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load business numbers from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.business_numbers = data.get("business_numbers", {})
                    logger.info(f"Loaded {len(self.business_numbers)} business numbers")
            else:
                logger.info("Business numbers config file not found, creating new one")
                self._create_default_config()
        
        except Exception as e:
            logger.error(f"Error loading business numbers config: {str(e)}")
            self.business_numbers = {}
    
    def _create_default_config(self) -> None:
        """Create default business numbers configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            default_config = {
                "business_numbers": {
                    "salon_main": {
                        "phone_id": "your_phone_id",
                        "phone_number": "+1-555-0100",
                        "display_name": "Salon Booking",
                        "business_name": "Salon Booking System",
                        "description": "Book salon appointments online",
                        "status": "active",
                        "created_at": datetime.now().isoformat(),
                        "features": ["booking", "search", "notifications"],
                        "supported_languages": ["en"],
                        "timezone": "UTC"
                    }
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self.business_numbers = default_config["business_numbers"]
            logger.info("Created default business numbers configuration")
        
        except Exception as e:
            logger.error(f"Error creating default config: {str(e)}")
    
    def _save_config(self) -> None:
        """Save business numbers to config file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {"business_numbers": self.business_numbers}
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Saved business numbers configuration")
        
        except Exception as e:
            logger.error(f"Error saving business numbers config: {str(e)}")
    
    def add_business_number(self, number_id: str, phone_data: Dict[str, Any]) -> bool:
        """
        Add a new business number
        
        Args:
            number_id: Unique identifier for the business number
            phone_data: Phone number configuration data
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if number_id in self.business_numbers:
                logger.warning(f"Business number {number_id} already exists")
                return False
            
            self.business_numbers[number_id] = {
                "phone_id": phone_data.get("phone_id"),
                "phone_number": phone_data.get("phone_number"),
                "display_name": phone_data.get("display_name", "Salon Booking"),
                "business_name": phone_data.get("business_name", "Salon Booking System"),
                "description": phone_data.get("description", "Book salon appointments"),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "features": phone_data.get("features", ["booking", "search"]),
                "supported_languages": phone_data.get("supported_languages", ["en"]),
                "timezone": phone_data.get("timezone", "UTC")
            }
            
            self._save_config()
            logger.info(f"Added business number: {number_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding business number: {str(e)}")
            return False
    
    def get_business_number(self, number_id: str) -> Optional[Dict[str, Any]]:
        """
        Get business number configuration
        
        Args:
            number_id: Business number identifier
        
        Returns:
            Business number data or None
        """
        return self.business_numbers.get(number_id)
    
    def get_all_business_numbers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all business numbers
        
        Returns:
            Dictionary of all business numbers
        """
        return self.business_numbers
    
    def update_business_number(self, number_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update business number configuration
        
        Args:
            number_id: Business number identifier
            updates: Fields to update
        
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if number_id not in self.business_numbers:
                logger.warning(f"Business number {number_id} not found")
                return False
            
            self.business_numbers[number_id].update(updates)
            self.business_numbers[number_id]["updated_at"] = datetime.now().isoformat()
            
            self._save_config()
            logger.info(f"Updated business number: {number_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating business number: {str(e)}")
            return False
    
    def delete_business_number(self, number_id: str) -> bool:
        """
        Delete business number
        
        Args:
            number_id: Business number identifier
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if number_id not in self.business_numbers:
                logger.warning(f"Business number {number_id} not found")
                return False
            
            del self.business_numbers[number_id]
            self._save_config()
            logger.info(f"Deleted business number: {number_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting business number: {str(e)}")
            return False
    
    def get_active_numbers(self) -> List[Dict[str, Any]]:
        """
        Get all active business numbers
        
        Returns:
            List of active business numbers
        """
        return [
            num for num in self.business_numbers.values()
            if num.get("status") == "active"
        ]
    
    def set_number_status(self, number_id: str, status: str) -> bool:
        """
        Set business number status
        
        Args:
            number_id: Business number identifier
            status: Status (active, inactive, suspended)
        
        Returns:
            True if updated successfully, False otherwise
        """
        if status not in ["active", "inactive", "suspended"]:
            logger.warning(f"Invalid status: {status}")
            return False
        
        return self.update_business_number(number_id, {"status": status})
    
    def add_feature(self, number_id: str, feature: str) -> bool:
        """
        Add feature to business number
        
        Args:
            number_id: Business number identifier
            feature: Feature to add
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if number_id not in self.business_numbers:
                return False
            
            features = self.business_numbers[number_id].get("features", [])
            if feature not in features:
                features.append(feature)
                self.business_numbers[number_id]["features"] = features
                self._save_config()
                logger.info(f"Added feature {feature} to {number_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error adding feature: {str(e)}")
            return False
    
    def remove_feature(self, number_id: str, feature: str) -> bool:
        """
        Remove feature from business number
        
        Args:
            number_id: Business number identifier
            feature: Feature to remove
        
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if number_id not in self.business_numbers:
                return False
            
            features = self.business_numbers[number_id].get("features", [])
            if feature in features:
                features.remove(feature)
                self.business_numbers[number_id]["features"] = features
                self._save_config()
                logger.info(f"Removed feature {feature} from {number_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error removing feature: {str(e)}")
            return False
    
    def get_number_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get business number by phone number
        
        Args:
            phone_number: Phone number to search
        
        Returns:
            Business number data or None
        """
        for num_id, num_data in self.business_numbers.items():
            if num_data.get("phone_number") == phone_number:
                return num_data
        
        return None
