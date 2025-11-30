"""
Location utilities - Calculate distance between coordinates using latitude and longitude
"""
import math
from typing import Tuple, Dict, List, Optional


class LocationCalculator:
    """Calculate distances and locations using latitude and longitude"""
    
    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371
    # Earth's radius in meters
    EARTH_RADIUS_M = 6371000
    
    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        unit: str = "km"
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            unit: Unit of distance ("km" or "m" or "miles")
            
        Returns:
            Distance between the two points
        """
        try:
            # Convert degrees to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            # Calculate distance based on unit
            if unit.lower() == "m":
                distance = LocationCalculator.EARTH_RADIUS_M * c
            elif unit.lower() == "miles":
                distance = (LocationCalculator.EARTH_RADIUS_KM * c) * 0.621371
            else:  # Default to km
                distance = LocationCalculator.EARTH_RADIUS_KM * c
            
            return round(distance, 2)
        
        except Exception as e:
            raise ValueError(f"Error calculating distance: {str(e)}")
    
    @staticmethod
    def distance_between_points(
        point1: Dict[str, float],
        point2: Dict[str, float],
        unit: str = "km"
    ) -> float:
        """
        Calculate distance between two points given as dictionaries
        
        Args:
            point1: Dictionary with 'latitude' and 'longitude' keys
            point2: Dictionary with 'latitude' and 'longitude' keys
            unit: Unit of distance ("km" or "m" or "miles")
            
        Returns:
            Distance between the two points
        """
        try:
            lat1 = point1.get("latitude") or point1.get("lat")
            lon1 = point1.get("longitude") or point1.get("lon")
            lat2 = point2.get("latitude") or point2.get("lat")
            lon2 = point2.get("longitude") or point2.get("lon")
            
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                raise ValueError("Missing latitude or longitude in point dictionaries")
            
            return LocationCalculator.haversine_distance(lat1, lon1, lat2, lon2, unit)
        
        except Exception as e:
            raise ValueError(f"Error calculating distance between points: {str(e)}")
    
    @staticmethod
    def is_within_radius(
        center_lat: float,
        center_lon: float,
        point_lat: float,
        point_lon: float,
        radius: float,
        unit: str = "km"
    ) -> bool:
        """
        Check if a point is within a given radius from center
        
        Args:
            center_lat: Latitude of center point
            center_lon: Longitude of center point
            point_lat: Latitude of point to check
            point_lon: Longitude of point to check
            radius: Radius distance
            unit: Unit of radius ("km" or "m" or "miles")
            
        Returns:
            True if point is within radius, False otherwise
        """
        distance = LocationCalculator.haversine_distance(
            center_lat,
            center_lon,
            point_lat,
            point_lon,
            unit
        )
        return distance <= radius
    
    @staticmethod
    def find_nearby_locations(
        center_lat: float,
        center_lon: float,
        locations: List[Dict],
        radius: float,
        unit: str = "km"
    ) -> List[Dict]:
        """
        Find all locations within a given radius from center
        
        Args:
            center_lat: Latitude of center point
            center_lon: Longitude of center point
            locations: List of location dictionaries with 'latitude' and 'longitude'
            radius: Radius distance
            unit: Unit of radius ("km" or "m" or "miles")
            
        Returns:
            List of locations within radius with distance calculated
        """
        nearby = []
        
        for location in locations:
            try:
                lat = location.get("latitude") or location.get("lat")
                lon = location.get("longitude") or location.get("lon")
                
                if lat is None or lon is None:
                    continue
                
                distance = LocationCalculator.haversine_distance(
                    center_lat,
                    center_lon,
                    lat,
                    lon,
                    unit
                )
                
                if distance <= radius:
                    location_copy = dict(location)
                    location_copy["distance"] = distance
                    location_copy["distance_unit"] = unit
                    nearby.append(location_copy)
            
            except Exception as e:
                continue
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance"])
        return nearby
    
    @staticmethod
    def get_bounding_box(
        center_lat: float,
        center_lon: float,
        radius: float,
        unit: str = "km"
    ) -> Dict[str, float]:
        """
        Get bounding box coordinates for a given center and radius
        
        Args:
            center_lat: Latitude of center point
            center_lon: Longitude of center point
            radius: Radius distance
            unit: Unit of radius ("km" or "m" or "miles")
            
        Returns:
            Dictionary with min/max latitude and longitude
        """
        # Convert radius to kilometers if needed
        if unit.lower() == "m":
            radius_km = radius / 1000
        elif unit.lower() == "miles":
            radius_km = radius / 0.621371
        else:
            radius_km = radius
        
        # Approximate degrees per km
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        return {
            "min_latitude": center_lat - lat_offset,
            "max_latitude": center_lat + lat_offset,
            "min_longitude": center_lon - lon_offset,
            "max_longitude": center_lon + lon_offset
        }
    
    @staticmethod
    def bearing_between_points(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate bearing (direction) from point 1 to point 2
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Bearing in degrees (0-360)
        """
        try:
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            dlon = lon2_rad - lon1_rad
            
            x = math.sin(dlon) * math.cos(lat2_rad)
            y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
            
            bearing = math.atan2(x, y)
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360
            
            return round(bearing, 2)
        
        except Exception as e:
            raise ValueError(f"Error calculating bearing: {str(e)}")


# Convenience functions
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float:
    """
    Quick function to calculate distance between two coordinates
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        unit: Unit of distance ("km" or "m" or "miles")
        
    Returns:
        Distance between the two points
    """
    return LocationCalculator.haversine_distance(lat1, lon1, lat2, lon2, unit)


def is_nearby(
    center_lat: float,
    center_lon: float,
    point_lat: float,
    point_lon: float,
    radius: float,
    unit: str = "km"
) -> bool:
    """
    Quick function to check if a point is within radius
    
    Args:
        center_lat: Latitude of center point
        center_lon: Longitude of center point
        point_lat: Latitude of point to check
        point_lon: Longitude of point to check
        radius: Radius distance
        unit: Unit of radius ("km" or "m" or "miles")
        
    Returns:
        True if point is within radius, False otherwise
    """
    return LocationCalculator.is_within_radius(center_lat, center_lon, point_lat, point_lon, radius, unit)


def find_nearby(
    center_lat: float,
    center_lon: float,
    locations: List[Dict],
    radius: float,
    unit: str = "km"
) -> List[Dict]:
    """
    Quick function to find nearby locations
    
    Args:
        center_lat: Latitude of center point
        center_lon: Longitude of center point
        locations: List of location dictionaries
        radius: Radius distance
        unit: Unit of radius ("km" or "m" or "miles")
        
    Returns:
        List of nearby locations sorted by distance
    """
    return LocationCalculator.find_nearby_locations(center_lat, center_lon, locations, radius, unit)
