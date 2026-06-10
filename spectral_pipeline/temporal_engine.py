import logging
from typing import Tuple, Dict, Any
import numpy as np

from spectral_pipeline.geocoder import SpatialGeocoder
from spectral_pipeline.adapter import Sentinel2Adapter
from spectral_pipeline.engine import SpectralEngine

# ── NEW: Import the Computer Vision Cluster Engine ──
from cv.kmeans_classifier import KMeansClassifier
from config import N_CLUSTERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TemporalChangeEngine:
    """
    v3 Core Calculator Engine. Operates on matrix mathematics transformations
    and applies unsupervised K-Means CV clustering for adaptive change detection.
    """

    def __init__(self, geocoder: SpatialGeocoder, adapter: Sentinel2Adapter, spectral_engine: SpectralEngine):
        self.geocoder = geocoder
        self.adapter  = adapter
        self.engine   = spectral_engine
        
        # ── NEW: Instantiate the CV Layer component ──
        self.classifier = KMeansClassifier(n_clusters=N_CLUSTERS)

    def execute_change_pipeline(
        self,
        location_query:  str,
        buffer_km:       float,
        target_index:    str,
        pre_date_window: str,
        post_date_window: str
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, list, dict]:
        """
        Coordinates data calculation pipeline: streams cubes, computes delta matrices,
        and hands execution off to the CV segmenter instead of legacy rule-based thresholds.
        """
        logging.info("=== INITIALIZING DUAL-DATE TEMPORAL MATH ENGINES ===")
        target_index = target_index.upper()

        bbox = self.geocoder.resolve_text_to_bbox(location_query, buffer_km=buffer_km)

        if target_index not in self.engine.recipes:
            raise ValueError(f"Target index '{target_index}' is not cataloged in the asset recipes ledger.")

        recipe = self.engine.recipes[target_index]
        resolution_m = recipe.get("resolution_m", 20)
        needed_bands = [recipe["A"], recipe["B"]]

        logging.info("Streaming Phase 1 Base Map Cube Array Matrix...")
        bands_pre = self.adapter.ingest_data(
            bbox=bbox, required_abstract_bands=needed_bands, time_window=pre_date_window, resolution_m=resolution_m
        )
        matrix_pre = self.engine.run(index_name=target_index, available_bands=bands_pre)

        logging.info("Streaming Phase 2 Comparison Cube Array Matrix...")
        bands_post = self.adapter.ingest_data(
            bbox=bbox, required_abstract_bands=needed_bands, time_window=post_date_window, resolution_m=resolution_m
        )
        matrix_post = self.engine.run(index_name=target_index, available_bands=bands_post)

        # Mathematical transformation: Pre minus Post
        delta_matrix = matrix_pre - matrix_post

        # ── NEW: Run Unsupervised CV Segmentation ──
        # This replaces the legacy hardcoded threshold loop block entirely!
        labels_2d, sorted_centroids = self.classifier.segment_delta(delta_matrix=delta_matrix)

        # ── NEW: Extract Adaptive Cluster Statistical Payloads ──
        stats_payload = self.classifier.generate_cluster_statistics(
            index_name=target_index,
            resolution_m=resolution_m,
            location_name=location_query
        )

        # We return the classified labels matrix in place of raw delta values to match layout constraints
        return matrix_pre, matrix_post, labels_2d, list(bbox), stats_payload