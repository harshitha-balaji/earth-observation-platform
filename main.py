import os
import logging
import webbrowser
from spectral_pipeline.geocoder import SpatialGeocoder
from spectral_pipeline.engine import SpectralEngine
from spectral_pipeline.adapter import Sentinel2Adapter
from spectral_pipeline.visualizer import MapVisualizer, TemporalMapVisualizer
from spectral_pipeline.temporal_engine import TemporalChangeEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_dynamic_user_inputs(engine: SpectralEngine):
    """Handles terminal setup configuration arrays."""
    print("\n" + "="*50)
    print("      EARTH OBSERVATION ENGINE v2.0 SUITE      ")
    print("="*50)
    
    print("\nSelect Operational Pipeline Mode:")
    print("  [1] Baseline Snapshot Exploration (v1 Core)")
    print("  [2] Multi-Temporal Side-by-Side Comparison (v2 Engine)")
    mode_choice = input("\nEnter choice option (1-2): ").strip()
    
    print("\n[Step 1] Specify Target Research Area:")
    user_query = input("  Enter location name (e.g., Lake Mead, Sriharikota, Munich): ").strip()
    if not user_query:
        user_query = "Sriharikota"

    print("\n[Step 2] Select Research Window Scale:")
    print("  1 -> Small  (5 km x 5 km tile)")
    print("  2 -> Medium (10 km x 10 km tile) [Default]")
    print("  3 -> Large  (20 km x 20 km tile)")
    scale_choice = input("  Select option (1-3): ").strip()
    
    if scale_choice == "1":
        buffer_km = 2.5
    elif scale_choice == "3":
        buffer_km = 10.0
    else:
        buffer_km = 5.0

    recipe_keys = list(engine.recipes.keys())
    print("\n[Step 3] Select Spectral Analysis Index:")
    for idx, key in enumerate(recipe_keys, start=1):
        print(f"  {idx} -> {key}: {engine.recipes[key]['desc']}")
        
    idx_choice = input(f"  Select option (1-{len(recipe_keys)}): ").strip()
    try:
        chosen_slot = int(idx_choice) - 1
        if 0 <= chosen_slot < len(recipe_keys):
            target_index = recipe_keys[chosen_slot]
        else:
            raise ValueError
    except ValueError:
        target_index = recipe_keys[0]

    return mode_choice, user_query, buffer_km, target_index


def main():
    try:
        geocoder = SpatialGeocoder()
        engine = SpectralEngine()
        adapter = Sentinel2Adapter()
        temporal_engine = TemporalChangeEngine(geocoder, adapter, engine)
        
        mode_choice, user_query, buffer_km, target_index = get_dynamic_user_inputs(engine)
        
        if mode_choice != "2":
            # === OPTION 1: CLASSIC SINGLE VIEW RENDER ===
            recipe = engine.recipes[target_index]
            needed_bands = [recipe["A"], recipe["B"]]
            bbox = geocoder.resolve_text_to_bbox(location_query=user_query, buffer_km=buffer_km)
            
            logging.info("LAUNCHING MULTI-SPECTRAL RUNTIME PIPELINE (MODE 1)")
            normalized_data = adapter.ingest_data(bbox=bbox, required_abstract_bands=needed_bands)
            result_matrix = engine.run(index_name=target_index, available_bands=normalized_data)
            stats_payload = engine.generate_spatial_statistics(matrix=result_matrix, index_name=target_index)
            
            clean_name = user_query.lower().replace(" ", "_").replace(",", "").replace(".", "")
            output_html = f"{clean_name}_{target_index.lower()}_map.html"
            
            html_page_path = MapVisualizer.create_interactive_html(
                matrix=result_matrix, bbox=bbox, index_name=target_index,
                stats_payload=stats_payload, output_filename=output_html
            )
            webbrowser.open(f"file://{os.path.abspath(html_page_path)}")
            
        else:
            # === OPTION 2: MULTI-TEMPORAL SIDE BY SIDE VIEW ===
            print("\n[Step 4] Configure Data Ingestion Custom Windows:")
            print("  Format Notation Syntax: YYYY-MM-DD/YYYY-MM-DD")
            pre_window = input("  Enter Pre-Event Baseline Date Range: ").strip()
            post_window = input("  Enter Post-Event Analysis Date Range: ").strip()
            
            if not pre_window: pre_window = "2026-01-01/2026-03-01"
            if not post_window: post_window = "2026-03-01/2026-05-01"
            
            # Fetch numeric data sets straight out of decoupled math blocks
            matrix_pre, matrix_post, delta_matrix, bbox, stats_payload = temporal_engine.execute_change_pipeline(
                location_query=user_query, buffer_km=buffer_km, target_index=target_index,
                pre_date_window=pre_window, post_date_window=post_window
            )
            
            clean_name = user_query.lower().replace(" ", "_").replace(",", "").replace(".", "")
            output_html = f"{clean_name}_side_by_side_{target_index.lower()}.html"
            
            # Wire calculations directly into our dedicated layout manager
            html_page_path = TemporalMapVisualizer.create_side_by_side_html(
                matrix_pre=matrix_pre, matrix_post=matrix_post, bbox=bbox,
                target_index=target_index, stats_payload=stats_payload, output_filename=output_html
            )
            webbrowser.open(f"file://{os.path.abspath(html_page_path)}")
            logging.info(">>> TEMPORAL COMPARISON WORKSPACE RUNNING SUCCESSFUL <<<")
            
    except Exception as e:
        logging.error("Pipeline collapsed during active runtime sequence: %s", e)
        raise


if __name__ == "__main__":
    main()