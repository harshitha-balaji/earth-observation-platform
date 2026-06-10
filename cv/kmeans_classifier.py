import logging
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.cluster import KMeans

from config import N_CLUSTERS

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")


class KMeansClassifier:
    """
    Scikit-Learn Powered Cluster Classification Engine.
    Segments multi-temporal delta matrix changes into adaptive environmental 
    disturbance profiles using high-performance machine learning frameworks.
    """

    def __init__(self, n_clusters: int = N_CLUSTERS, max_iter: int = 100):
        self.n_clusters = n_clusters
        
        # Initialize standard Scikit-Learn KMeans pipeline with a fixed seed 
        # to ensure deterministic behavior across workspace updates.
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            init="k-means++",
            max_iter=max_iter,
            random_state=42,
            n_init="auto"
        )
        
        # State placeholders to hold synchronized arrays after clustering completes
        self.centroids: np.ndarray = np.array([])
        
    def segment_delta(self, delta_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Processes a raw 2D change matrix, isolates active valid pixels from data gaps, 
        converges clusters via scikit-learn, and guarantees ordered centroid tracking.
        
        Returns:
            Tuple[labels_2d, sorted_centroids]: 
                labels_2d: Reconstructed 2D image matching the original shape.
                sorted_centroids: Chronologically aligned cluster means.
        """
        logging.info("Initializing CV Segmentation Loop on %dx%d Delta Matrix...", *delta_matrix.shape)
        
        # 1. Isolate invalid / masked data bounds (e.g. cloud masks or NODATA fill values)
        nan_mask = np.isnan(delta_matrix) | np.isinf(delta_matrix)
        valid_pixels = delta_matrix[~nan_mask]
        
        if valid_pixels.size == 0:
            raise ValueError("CV Error: Provided delta matrix contains no valid spatial telemetry pixels.")
            
        # 2. Reshape vector array to 2D column shape expected by Scikit-Learn (n_samples, n_features)
        data_features = valid_pixels.reshape(-1, 1)
        
        # 3. Fit the model and extract initial cluster results
        logging.info("Executing K-Means Convergence over %d valid data points...", data_features.shape[0])
        raw_labels = self.kmeans.fit_predict(data_features)
        raw_centroids = self.kmeans.cluster_centers_.flatten()
        
        # 4. Enforce Cluster Indeterminacy Protection: Sort clusters from lowest value to highest.
        # This guarantees Label 0 always means "Max Loss" and Label 3 means "Max Gain".
        sort_order = np.argsort(raw_centroids)
        self.centroids = raw_centroids[sort_order]
        
        # Remap the unsorted pixel labels to match our clean, ordered tracking schema
        label_mapping = {raw_id: schema_id for schema_id, raw_id in enumerate(sort_order)}
        mapped_labels = np.array([label_mapping[label] for label in raw_labels])
        
        # 5. Reconstruct full 2D spatial canvas, preserving original data gaps as a fallback index (-1)
        self.labels_2d = np.full(delta_matrix.shape, fill_value=-1, dtype=np.int8)
        self.labels_2d[~nan_mask] = mapped_labels
        
        logging.info("Unsupervised Segmentation Converged. Sorted Centroids: %s", self.centroids)
        return self.labels_2d, self.centroids
    
    def generate_cluster_statistics(
        self, 
        index_name: str, 
        resolution_m: int, 
        location_name: str
    ) -> Dict[str, Any]:
        """
        Calculates localized surface cover area metrics (km²) and percentages 
        for each sorted adaptive cluster channel to pass cleanly to UI visualizers.
        """
        # Ensure model execution has been completed before running statistical summaries
        if self.labels_2d.size == 0 or self.centroids.size == 0:
            raise ValueError("CV Error: Cannot profile statistics before running segment_delta().")

        # 1. Calculate area metrics based on the sensor's native meter resolution bounds
        total_pixels = np.sum(self.labels_2d != -1)  # Focus purely on valid active imagery
        pixel_area_km2 = (resolution_m * resolution_m) / 1_000_000.0

        # 2. Map structural names to our guaranteed sorted cluster levels
        cluster_metadata = {
            0: {"label": "Severe Disturbance / Loss", "color": "#d73027"},
            1: {"label": "Minor Disturbance / Shift", "color": "#f46d43"},
            2: {"label": "Stable Surface / Baseline", "color": "#fee08b"},
            3: {"label": "Active Growth / Recovery",  "color": "#66bd63"}
        }

        class_distribution = []
        
        # 3. Dynamic profiling sweep across our active cluster channels
        for cluster_id in range(self.n_clusters):
            pixel_count = int(np.sum(self.labels_2d == cluster_id))
            percentage = round((pixel_count / total_pixels) * 100, 2) if total_pixels > 0 else 0.0
            area_km2 = round(pixel_count * pixel_area_km2, 4)
            centroid_val = round(float(self.centroids[cluster_id]), 4)

            # Pull permanent descriptive keys mapped cleanly to sorted hierarchy
            meta = cluster_metadata.get(cluster_id, {"label": f"Cluster {cluster_id}", "color": "#ffffff"})

            class_distribution.append({
                "cluster_id": cluster_id,
                "label":       f"{meta['label']} (μ: {centroid_val})",
                "percentage":  percentage,
                "area_km2":    area_km2,
                "color":       meta["color"]
            })

        # 4. Return structured layout seamlessly matching our downstream map orchestration layer
        return {
            "index_name":          f"d{index_name} (Unsupervised K-Means)",
            "description":         f"Adaptive spatial cluster analysis for {location_name}.",
            "resolution_m":        resolution_m,
            "summary_metrics": {
                "min":  round(float(np.min(self.centroids)), 4),
                "max":  round(float(np.max(self.centroids)), 4),
                "mean": round(float(np.mean(self.centroids)), 4)
            },
            "class_distribution": class_distribution  # <-- Updated from "classes"
        }