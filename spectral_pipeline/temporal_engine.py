import logging
from typing import Tuple, Dict, Any
import numpy as np

from spectral_pipeline.geocoder import SpatialGeocoder
from spectral_pipeline.adapter import Sentinel2Adapter
from spectral_pipeline.engine import SpectralEngine
from config import TEMPORAL_CHANGE_BINS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TemporalChangeEngine:
    """
    v2 Core Calculator Engine. Operates purely on matrix mathematics transformations,
    decoupled from any HTML presentation layouts or map plotting layers.
    """

    def __init__(self, geocoder: SpatialGeocoder, adapter: Sentinel2Adapter, spectral_engine: SpectralEngine):
        self.geocoder = geocoder
        self.adapter  = adapter
        self.engine   = spectral_engine

    def execute_change_pipeline(
        self,
        location_query:  str,
        buffer_km:       float,
        target_index:    str,
        pre_date_window: str,
        post_date_window: str
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, list, dict]:
        """
        Coordinates the data calculation pipeline: queries bounds, streams dual cubes,
        runs differential delta matrices, and returns arrays directly to the system router.
        """
        logging.info("=== INITIALIZING DUAL-DATE TEMPORAL MATH ENGINES ===")
        target_index = target_index.upper()

        bbox = self.geocoder.resolve_text_to_bbox(location_query, buffer_km=buffer_km)

        if target_index not in self.engine.recipes:
            raise ValueError(f"Target index configuration index '{target_index}' does not exist.")

        recipe         = self.engine.recipes[target_index]
        required_bands = [recipe["A"], recipe["B"]]
        resolution_m   = recipe.get("resolution_m", 10)

        logging.info("Pulling Pre-Event Baseline State within window: %s", pre_date_window)
        pre_data   = self.adapter.ingest_data(
            bbox=bbox,
            required_abstract_bands=required_bands,
            time_window=pre_date_window,
            resolution_m=resolution_m
        )
        matrix_pre = self.engine.run(index_name=target_index, available_bands=pre_data)

        logging.info("Pulling Post-Event Monitoring State within window: %s", post_date_window)
        post_data   = self.adapter.ingest_data(
            bbox=bbox,
            required_abstract_bands=required_bands,
            time_window=post_date_window,
            resolution_m=resolution_m
        )
        matrix_post = self.engine.run(index_name=target_index, available_bands=post_data)

        delta_matrix  = matrix_pre - matrix_post
        stats_payload = self._generate_change_statistics(
            delta_matrix=delta_matrix,
            index_name=target_index,
            resolution_m=resolution_m,
            location_name=location_query
        )

        return matrix_pre, matrix_post, delta_matrix, bbox, stats_payload

    def _generate_change_statistics(
        self,
        delta_matrix: np.ndarray,
        index_name:   str,
        resolution_m: int,
        location_name: str
    ) -> Dict[str, Any]:
        """Classifies matrix delta variances out to discrete metric surface cover boundaries (km²)."""
        total_pixels    = delta_matrix.size
        pixel_area_km2  = (resolution_m * resolution_m) / 1_000_000.0

        class_distribution = []
        for bin_def in TEMPORAL_CHANGE_BINS:
            mask        = (delta_matrix >= bin_def["min"]) & (delta_matrix < bin_def["max"])
            pixel_count = int(np.sum(mask))
            percentage  = round((pixel_count / total_pixels) * 100, 2)
            area_km2    = round(pixel_count * pixel_area_km2, 4)

            class_distribution.append({
                "label":      bin_def["label"],
                "percentage": percentage,
                "area_km2":   area_km2,
            })

        return {
            "index_name":   f"d{index_name} (Differential Scale)",
            "description":  f"Multi-temporal delta profile for {location_name}.",
            "resolution_m": resolution_m,
            "summary_metrics": {
                "min":  round(float(np.min(delta_matrix)),  4),
                "max":  round(float(np.max(delta_matrix)),  4),
                "mean": round(float(np.mean(delta_matrix)), 4),
            },
            "class_distribution": class_distribution,
        }
