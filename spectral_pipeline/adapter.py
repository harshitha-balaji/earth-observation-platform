from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional
import numpy as np

from pystac_client import Client
import odc.stac


class SatelliteAdapter(ABC):
    """
    Abstract Base Class acting as the unified translation gateway.
    Supports variable time windows and explicit output resolution control
    for multi-temporal grid alignment.
    """
    def __init__(self, band_mapping: Dict[str, str]):
        self.band_mapping = band_mapping
        self.hardware_lookup = {v: k for k, v in band_mapping.items()}

    @abstractmethod
    def fetch_spatial_window(
        self,
        bbox: Tuple[float, float, float, float],
        bands: List[str],
        time_window: str,
        resolution_m: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        pass

    def ingest_data(
        self,
        bbox: Tuple[float, float, float, float],
        required_abstract_bands: List[str],
        time_window: str = "2026-01-01/2026-05-01",
        resolution_m: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Translates abstract band names to hardware asset keys, fetches the scene,
        and returns a normalised abstract-keyed payload.

        resolution_m is forwarded so odc.stac.load uses a fixed output grid for
        every acquisition — critical for temporal comparisons where pre and post
        scenes must have identical array shapes for pixel-wise subtraction.
        """
        hardware_bands_to_fetch = [self.hardware_lookup[band] for band in required_abstract_bands]
        raw_hardware_payload = self.fetch_spatial_window(bbox, hardware_bands_to_fetch, time_window, resolution_m)

        normalized_payload: Dict[str, np.ndarray] = {}
        for hardware_key, matrix in raw_hardware_payload.items():
            abstract_key = self.band_mapping[hardware_key]
            normalized_payload[abstract_key] = matrix

        return normalized_payload


class Sentinel2Adapter(SatelliteAdapter):
    """
    Concrete implementation for the AWS Earth Search Sentinel-2 L2A STAC catalog.

    Asset key names match the Element84 v1 schema exactly (lowercase common names).
    The NIR band used here is the broad 10m Band 8 ("nir"), not the narrow 20m
    Band 8A ("nir08"), to keep NDVI, NDWI at 10m native resolution.
    """
    def __init__(self):
        sentinel_2_bands = {
            "blue":   "BLUE",
            "green":  "GREEN",
            "red":    "RED",
            "nir":    "NIR",      # Band 8  — 10m
            "swir16": "SWIR",     # Band 11 — 20m
            "swir22": "SWIR2"     # Band 12 — 20m
        }
        super().__init__(band_mapping=sentinel_2_bands)
        self.stac_endpoint = "https://earth-search.aws.element84.com/v1"

    def fetch_spatial_window(
        self,
        bbox: Tuple[float, float, float, float],
        bands: List[str],
        time_window: str,
        resolution_m: Optional[int] = None
    ) -> Dict[str, np.ndarray]:
        """
        Streams a cloud-native pixel window from the AWS STAC catalog.

        CRS / resolution strategy
        ─────────────────────────
        odc.stac.load is designed for projected coordinate systems with resolution
        expressed in metres. Passing crs="EPSG:4326" with a degree-converted
        resolution causes it to silently return all-zero arrays — which is why the
        overlay appeared white and all stats showed 0.0.

        Fix: use EPSG:3857 (Web Mercator, metres) as the output CRS with resolution
        in metres. This is the same projection Leaflet/OSM uses, so the resulting
        array aligns perfectly with the folium ImageOverlay bounds without any
        reprojection artefacts. When no resolution is specified (single-snapshot
        mode), we let odc.stac infer the native resolution from the scene metadata,
        which is always valid for single-scene loads.
        """
        catalog = Client.open(self.stac_endpoint)

        search_query = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=time_window,
            query={"eo:cloud_cover": {"lt": 5}},
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}]
        )

        search_items = list(search_query.item_collection())
        if not search_items:
            raise RuntimeError(
                f"No cloud-optimized Sentinel-2 items found within window: {time_window}. "
                "Try relaxing the cloud cover threshold or expanding the date range."
            )

        target_scene = search_items[0]

        # Always project into Web Mercator (metres) — compatible with Leaflet's
        # tile coordinate system and safe for odc.stac's metre-based resolution engine.
        load_kwargs = dict(
            bands=bands,
            bbox=bbox,
            chunks={},
            fail_on_error=False,
            crs="EPSG:3857",
        )

        # Only pin resolution when explicitly requested (temporal mode).
        # Single-snapshot mode lets odc.stac use the scene's native resolution,
        # avoiding the empty-array bug while still producing correct output.
        if resolution_m is not None:
            load_kwargs["resolution"] = resolution_m

        spatial_data_cube = odc.stac.load([target_scene], **load_kwargs)

        hardware_payload: Dict[str, np.ndarray] = {}
        for hardware_band in bands:
            raw_matrix = spatial_data_cube[hardware_band].isel(time=0).values
            hardware_payload[hardware_band] = raw_matrix.astype(float)

        return hardware_payload
