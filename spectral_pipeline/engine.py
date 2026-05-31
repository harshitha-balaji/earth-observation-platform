import os
import json
import logging
from typing import Dict, Any, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SpectralEngine:
    """
    A modular, high-performance computing engine designed to process multi-spectral 
    satellite arrays by dynamically loading mathematical recipes and classification
    threshold definitions from an external configuration schema.
    """

    def __init__(self, config_name: str = "recipes.json") -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(current_dir, config_name)
        
        self.recipes = self._load_recipes_config()

    def _load_recipes_config(self) -> dict:
        """Loads index configurations and statistical classes from the local JSON file."""
        if not os.path.exists(self.config_path):
            logging.warning("Config file '%s' not found. Falling back to an internal default.", self.config_path)
            return {
                "NDVI": {
                    "desc": "Vegetation Index (Fallback)", 
                    "A": "NIR", 
                    "B": "RED",
                    "resolution_m": 10,
                    "classes": [{"label": "Default Base Class", "min": -1.0, "max": 1.0}]
                }
            }
            
        with open(self.config_path, "r") as f:
            try:
                recipes_book = json.load(f)
                logging.info("Successfully registered %d spectral recipes from config file.", len(recipes_book))
                return recipes_book
            except json.JSONDecodeError as e:
                logging.error("Malformed configuration file. Check your JSON syntax: %s", e)
                raise

    def calculate_normalized_difference(self, band_A: np.ndarray, band_B: np.ndarray) -> np.ndarray:
        """Computes the standard normalized difference ratio: (A - B) / (A + B)"""
        A = band_A.astype(np.float64)
        B = band_B.astype(np.float64)
        
        numerator = A - B
        denominator = A + B
        
        with np.errstate(divide='ignore', invalid='ignore'):
            index_matrix = numerator / denominator
            # Clean up out-of-bounds anomalies or blank imagery boundary artifacts
            index_matrix = np.nan_to_num(index_matrix, nan=0.0, posinf=0.0, neginf=0.0)
            
        return index_matrix

    def generate_spatial_statistics(self, matrix: np.ndarray, index_name: str) -> Dict[str, Any]:
        """
        Parses a computed index matrix using the current recipe thresholds to calculate
        the exact surface area coverage, percentage distribution, and descriptive matrix
        properties.
        """
        target_index = index_name.upper()
        recipe = self.recipes[target_index]
        classes_config = recipe.get("classes", [])

        # 1. Compute baseline matrix metrics using high-performance NumPy optimization
        total_pixels = matrix.size
        min_val = float(np.min(matrix))
        max_val = float(np.max(matrix))
        mean_val = float(np.mean(matrix))

        # 2. Derive pixel footprint from the recipe's declared sensor resolution.
        resolution_m = recipe.get("resolution_m", 10)
        SQ_METERS_PER_PIXEL = float(resolution_m ** 2)
        SQ_KM_CONVERSION_FACTOR = 1_000_000.0

        logging.info(
            "Pixel area for %s set to %.0f m² (resolution: %d m per pixel).",
            target_index, SQ_METERS_PER_PIXEL, resolution_m
        )

        distribution_breakdown = []

        # 3. Step through our configuration classes to slice our matrix array
        for cls in classes_config:
            label = cls["label"]
            lower_bound = cls["min"]
            upper_bound = cls["max"]
            
            # Create a high-performance boolean truth mask array over the pixel grid
            pixel_match_mask = (matrix >= lower_bound) & (matrix < upper_bound)
            matched_pixel_count = int(np.sum(pixel_match_mask))
            
            # Convert matching counts into raw spatial area metrics
            percentage = (matched_pixel_count / total_pixels) * 100.0
            area_sq_km = (matched_pixel_count * SQ_METERS_PER_PIXEL) / SQ_KM_CONVERSION_FACTOR
            
            distribution_breakdown.append({
                "label": label,
                "percentage": round(percentage, 2),
                "area_km2": round(area_sq_km, 2),
                "pixel_count": matched_pixel_count
            })

        # Pack the payload together to be routed into the mapping visualizer
        stats_payload = {
            "index_name": target_index,
            "description": recipe["desc"],
            "resolution_m": resolution_m,
            "summary_metrics": {
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "mean": round(mean_val, 4)
            },
            "class_distribution": distribution_breakdown
        }
        
        logging.info("Spatial analytics compilation complete for index: %s", target_index)
        return stats_payload

    def run(self, index_name: str, available_bands: Dict[str, np.ndarray]) -> np.ndarray:
        """Validates the user's request, verifies the data inventory, and dynamically routes matrices to the math formula."""
        target_index = index_name.upper()
        
        if target_index not in self.recipes:
            valid_options = list(self.recipes.keys())
            raise ValueError(
                f"Unsupported index: '{index_name}'. "
                f"Please choose a valid recipe from: {valid_options}"
            )
            
        recipe = self.recipes[target_index]
        required_A = recipe["A"]
        required_B = recipe["B"]
        
        if required_A not in available_bands or required_B not in available_bands:
            provided_bands = list(available_bands.keys())
            raise KeyError(
                f"Data Inventory Error: Cannot calculate {target_index}. "
                f"Formula requires '{required_A}' and '{required_B}' bands. "
                f"You only provided: {provided_bands}"
            )
            
        logging.info("Routing confirmed: Executing %s (%s vs %s).", target_index, required_A, required_B)
        
        matrix_A = available_bands[required_A]
        matrix_B = available_bands[required_B]
        
        return self.calculate_normalized_difference(matrix_A, matrix_B)
