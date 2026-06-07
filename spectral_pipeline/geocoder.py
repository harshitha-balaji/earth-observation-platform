import logging
from typing import Tuple
import numpy as np
from geopy.geocoders import Nominatim

from config import (
    GEOCODER_USER_AGENT,
    GEOCODER_TIMEOUT_SECONDS,
    KM_PER_DEGREE_LATITUDE,
    BBOX_COORDINATE_PRECISION,
    DEFAULT_BUFFER_KM,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SpatialGeocoder:
    """
    Handles resolving plain text location queries into precise,
    aspect-ratio-locked geographic bounding boxes using public directory layers.
    """

    def __init__(self, user_agent: str = GEOCODER_USER_AGENT):
        self.geolocator = Nominatim(user_agent=user_agent)

    def resolve_text_to_bbox(
        self, location_query: str, buffer_km: float = DEFAULT_BUFFER_KM
    ) -> Tuple[float, float, float, float]:
        """
        Translates a human-readable text string into a strictly bounded coordinate frame.
        Returns: (min_lon, min_lat, max_lon, max_lat)
        """
        logging.info("Contacting Geocoding registry to locate target: '%s'...", location_query)

        location = self.geolocator.geocode(location_query, timeout=GEOCODER_TIMEOUT_SECONDS)

        if not location:
            raise ValueError(
                f"Geocoding Error: Could not locate '{location_query}' anywhere in the directory. "
                "Please check the spelling or try a more prominent landmark."
            )

        center_lat = location.latitude
        center_lon = location.longitude
        logging.info(
            "Location resolved successfully! Center Point found at -> Lat: %.5f, Lon: %.5f",
            center_lat, center_lon
        )

        # Fixed baseline conversion: 1 degree latitude ≈ 111 km
        delta_latitude  = buffer_km / KM_PER_DEGREE_LATITUDE

        # Adaptive East-West offset corrected for Earth's curvature at this latitude
        lat_radians     = np.radians(center_lat)
        delta_longitude = buffer_km / (KM_PER_DEGREE_LATITUDE * np.cos(lat_radians))

        bbox = (
            float(np.round(center_lon - delta_longitude, BBOX_COORDINATE_PRECISION)),
            float(np.round(center_lat - delta_latitude,  BBOX_COORDINATE_PRECISION)),
            float(np.round(center_lon + delta_longitude, BBOX_COORDINATE_PRECISION)),
            float(np.round(center_lat + delta_latitude,  BBOX_COORDINATE_PRECISION)),
        )

        logging.info("Spatial buffer matrix generated: %s", bbox)
        return bbox
