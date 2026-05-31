import logging
from typing import Tuple
import numpy as np
from geopy.geocoders import Nominatim

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SpatialGeocoder:
    """
    Handles resolving plain text location queries into precise, 
    aspect-ratio-locked geographic bounding boxes using public directory layers.
    """
    
    def __init__(self, user_agent: str = "satellite_pipeline_explorer"):
        # Initialize the OpenStreetMap Nominatim engine with a unique user agent identifier
        self.geolocator = Nominatim(user_agent=user_agent)
        
    def resolve_text_to_bbox(self, location_query: str, buffer_km: float = 5.0) -> Tuple[float, float, float, float]:
        """
        Translates a human-readable text string into a strictly bounded coordinate frame.
        Returns: (min_lon, min_lat, max_lon, max_lat)
        """
        logging.info("Contacting Geocoding registry to locate target: '%s'...", location_query)
        
        # 1. Forward Geocoding: Look up the plain-text query
        location = self.geolocator.geocode(location_query, timeout=10)
        
        if not location:
            raise ValueError(
                f"Geocoding Error: Could not locate '{location_query}' anywhere in the directory. "
                "Please check the spelling or try a more prominent landmark."
            )
            
        center_lat = location.latitude
        center_lon = location.longitude
        logging.info("Location resolved successfully! Center Point found at -> Lat: %.5f, Lon: %.5f", center_lat, center_lon)
        
        # 2. Dynamic Spatial Delta Mathematics
        # Fixed baseline conversion factor: 1 degree of Latitude is always ~111 km
        KM_PER_DEGREE_LATITUDE = 111.0
        
        # Calculate the uniform offset for the North-South dimension
        delta_latitude = buffer_km / KM_PER_DEGREE_LATITUDE
        
        # Calculate the adaptive offset for the East-West dimension based on earth curvature
        lat_radians = np.radians(center_lat)
        delta_longitude = buffer_km / (KM_PER_DEGREE_LATITUDE * np.cos(lat_radians))
        
        # 3. Assemble the 4-point Coordinate Frame Matrix
        min_lon = center_lon - delta_longitude
        min_lat = center_lat - delta_latitude
        max_lon = center_lon + delta_longitude
        max_lat = center_lat + delta_latitude
        
        # Force high-precision coordinate rounding to match standard multi-spectral telemetry formats
        bbox = (
            float(np.round(min_lon, 4)),
            float(np.round(min_lat, 4)),
            float(np.round(max_lon, 4)),
            float(np.round(max_lat, 4))
        )
        
        logging.info("Spatial buffer matrix generated (10x10km tile envelope): %s", bbox)
        return bbox