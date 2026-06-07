import os

from spectral_pipeline.visualizer import (
    MapVisualizer,
    TemporalMapVisualizer
)
from config import (
    DEFAULT_BUFFER_KM,
    DEFAULT_TIME_WINDOW,
    TEMPORAL_PRE_WINDOW_DEFAULT,
    TEMPORAL_POST_WINDOW_DEFAULT,
)


class CommandExecutor:

    def __init__(self, geocoder, adapter, engine, temporal_engine):
        self.geocoder        = geocoder
        self.adapter         = adapter
        self.engine          = engine
        self.temporal_engine = temporal_engine

    def execute(self, route: dict) -> str:
        """
        Executes the routed pipeline instructions and returns the absolute path
        to the generated HTML map asset for native UI rendering.
        """
        pipeline = route["pipeline"]

        if pipeline == "snapshot":
            return self._execute_snapshot(route)

        elif pipeline == "temporal":
            return self._execute_temporal(route)

        raise ValueError(f"Unsupported pipeline: {pipeline}")

    def _execute_snapshot(self, route: dict) -> str:
        location  = route["location"]
        index     = route["index"]
        buffer_km = route.get("buffer_km", DEFAULT_BUFFER_KM)

        recipe       = self.engine.recipes[index]
        needed_bands = [recipe["A"], recipe["B"]]

        bbox = self.geocoder.resolve_text_to_bbox(location, buffer_km=buffer_km)

        raw_bands = self.adapter.ingest_data(
            bbox=bbox,
            required_abstract_bands=needed_bands,
            time_window=DEFAULT_TIME_WINDOW
        )

        index_matrix  = self.engine.run(index, raw_bands)
        stats_payload = self.engine.generate_spatial_statistics(index_matrix, index)

        clean_name    = self._clean_location_name(location)
        output_html   = f"{clean_name}_snapshot_{index.lower()}.html"

        html_page_path = MapVisualizer.create_interactive_html(
            matrix=index_matrix,
            bbox=bbox,
            index_name=index,
            stats_payload=stats_payload,
            output_filename=output_html
        )

        return html_page_path

    def _execute_temporal(self, route: dict) -> str:
        location  = route["location"]
        index     = route["index"]
        buffer_km = route.get("buffer_km", DEFAULT_BUFFER_KM)

        # Use parsed windows from NLP; fall back to config defaults if absent
        pre_window  = route.get("pre_window")  or TEMPORAL_PRE_WINDOW_DEFAULT
        post_window = route.get("post_window") or TEMPORAL_POST_WINDOW_DEFAULT

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

        return html_page_path

    @staticmethod
    def _clean_location_name(location: str) -> str:
        return (
            location.lower()
            .replace(" ", "_")
            .replace(",", "")
            .replace(".", "")
        )
