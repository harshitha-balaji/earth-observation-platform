import os
from nlp.routes import BaseRoute, SnapshotRoute, TemporalRoute
from spectral_pipeline.visualizer import MapVisualizer, TemporalMapVisualizer

class CommandExecutor:

    def __init__(self, geocoder, adapter, engine, temporal_engine) -> None:
        self.geocoder        = geocoder
        self.adapter         = adapter
        self.engine          = engine
        self.temporal_engine = temporal_engine

    def execute(self, route: BaseRoute) -> dict:
        """
        Accepts a strongly typed route instance, safely inspects the subclass mapping,
        and hands execution off to target underlying matrix mathematics blocks.
        """
        if isinstance(route, SnapshotRoute):
            return self._execute_snapshot(route)
        elif isinstance(route, TemporalRoute):
            return self._execute_temporal(route)

        raise ValueError(f"Unsupported pipeline transaction: {type(route).__name__}")

    def _execute_snapshot(self, route: SnapshotRoute) -> dict:
        location  = route.location
        index     = route.index
        buffer_km = route.buffer_km

        recipe = self.engine.recipes.get(index)

        if recipe is None:
            raise ValueError(f"Unknown index: {index}. Available: {list(self.engine.recipes.keys())}")
        
        needed_bands = [recipe["A"], recipe["B"]]

        bbox = self.geocoder.resolve_text_to_bbox(location, buffer_km=buffer_km)

        raw_bands = self.adapter.ingest_data(
            bbox=bbox,
            required_abstract_bands=needed_bands,
        )

        matrix_out = self.engine.run(index_name=index, available_bands=raw_bands)
        
        stats_payload = self.engine.generate_spatial_statistics(
            matrix=matrix_out,
            index_name=index
        )

        clean_name  = self._clean_location_name(location)
        output_html = f"{clean_name}_snapshot_{index.lower()}.html"

        # ── FIXED: Aligned method call to match create_interactive_html in visualizer.py ──
        html_page_path = MapVisualizer.create_interactive_html(
            matrix=matrix_out,
            bbox=bbox,
            index_name=index,
            stats_payload=stats_payload,
            output_filename=output_html
        )

        return {
            "map_path": html_page_path,
            "stats_payload": stats_payload,
            "metadata": {
                    "location": location,
                    "index": index,
                    "pipeline": "snapshot",
                    "buffer_km": buffer_km,
                }
            }

    def _execute_temporal(self, route: TemporalRoute) -> dict:
        location  = route.location
        index     = route.index
        buffer_km = route.buffer_km
        
        pre_window  = route.pre_window
        post_window = route.post_window

        (
            matrix_pre,
            matrix_post,
            delta_matrix,
            bbox,
            stats_payload
        ) = self.temporal_engine.execute_change_pipeline(
            location_query=location,
            buffer_km=buffer_km,
            target_index=index,
            pre_date_window=pre_window,
            post_date_window=post_window
        )

        clean_name  = self._clean_location_name(location)
        output_html = f"{clean_name}_side_by_side_{index.lower()}.html"

        html_page_path = TemporalMapVisualizer.create_side_by_side_html(
            matrix_pre=matrix_pre,
            matrix_post=matrix_post,
            bbox=bbox,
            target_index=index,
            stats_payload=stats_payload,
            output_filename=output_html
        )

        return {
            "map_path": html_page_path,
            "stats_payload": stats_payload,
            "metadata": {
                    "location": location,
                    "index": index,
                    "pipeline": "temporal",
                    "buffer_km": buffer_km,
                    "pre_window": pre_window,
                    "post_window": post_window,
                    }
        }

    @staticmethod
    def _clean_location_name(location: str) -> str:
        return location.replace(" ", "_").replace(",", "").lower()