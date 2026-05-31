import os
import logging
import folium
from folium import plugins
from branca.element import MacroElement
from jinja2 import Template
import numpy as np
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


STYLING_REGISTRY = {
    "NDVI":  {"cmap": "YlGn",   "vmin": -0.1, "vmax": 0.8},
    "NDWI":  {"cmap": "YlGnBu", "vmin":  0.0, "vmax": 0.6},
    "NDBI":  {"cmap": "YlOrRd", "vmin": -0.2, "vmax": 0.4},
    "NBR":   {"cmap": "PuRd",   "vmin": -0.4, "vmax": 0.7},
    "NDSI":  {"cmap": "Blues",  "vmin":  0.1, "vmax": 0.9}
}

_BASE_DARK_STYLE = (
    "<style>"
    "html, body { background-color: #1a1a1a !important; margin: 0; padding: 0; }"
    ".leaflet-container { background: #1a1a1a !important; }"
    ".folium-map { background-color: #1a1a1a !important; }"
    ".leaflet-pane.leaflet-masked-base-pane-pane { clip-path: inset(0px 0px 0px 0px); }"
    ".leaflet-pane.leaflet-pane-left-clip-pane { clip-path: inset(0px 0px 0px 0px); }"
    ".leaflet-pane.leaflet-pane-right-clip-pane { clip-path: inset(0px 0px 0px 0px); }"
    "</style>"
)


def _apply_colormap(matrix: np.ndarray, style: dict) -> np.ndarray:
    """Rescales an input index matrix and applies a Matplotlib colormap to build an RGBA layer."""
    rescaled = (matrix - style["vmin"]) / (style["vmax"] - style["vmin"])
    rescaled = np.clip(rescaled, 0.0, 1.0)
    colormap = plt.get_cmap(style["cmap"])
    return colormap(rescaled)


def _add_bounded_tilelayer(map_obj: folium.Map, pane_name: str, bounds: list):
    """Enforces a clean layout by confining tile delivery inside a strict container pane."""
    folium.map.CustomPane(pane_name, z_index=200).add_to(map_obj)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap contributors",
        pane=pane_name,
        overlay=False,
        control=False
    ).add_to(map_obj)


class DashboardOverlay(MacroElement):
    """
    Injects a responsive HTML/CSS dashboard panel directly into the Folium map layout canvas
    to render dynamic statistical data distributions over the viewport.
    """
    def __init__(self, stats_data: dict):
        super().__init__()
        self.stats = stats_data

        rows_html = ""
        for item in self.stats["class_distribution"]:
            rows_html += (
                "<tr>"
                f"<td style='padding: 6px 0; border-bottom: 1px solid #444;'>⚡ {item['label']}</td>"
                f"<td style='padding: 6px 0; text-align: right; border-bottom: 1px solid #444; font-weight: bold; color: #4CAF50;'>{item['percentage']}%</td>"
                f"<td style='padding: 6px 0; text-align: right; border-bottom: 1px solid #444; color: #aaa;'>{item['area_km2']} km²</td>"
                "</tr>"
            )

        index_name   = self.stats["index_name"]
        description  = self.stats["description"]
        resolution_m = self.stats.get("resolution_m", 10)
        
        metrics = self.stats.get("summary_metrics", {})
        val_max = metrics.get("max", "N/A")
        val_min = metrics.get("min", "N/A")
        val_mean = metrics.get("mean", "N/A")

        extra_metrics_html = ""
        if val_max != "N/A":
            extra_metrics_html = f"""
                <div style='border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; font-size: 12px; color: #eee;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
                        <span>Matrix Max Intensity:</span>
                        <span style='font-family: monospace; font-weight: bold; color: #ff9800;'>{val_max}</span>
                    </div>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
                        <span>Matrix Min Intensity:</span>
                        <span style='font-family: monospace; font-weight: bold; color: #2196F3;'>{val_min}</span>
                    </div>
                    <div style='display: flex; justify-content: space-between;'>
                        <span>Mean Footprint Value:</span>
                        <span style='font-family: monospace; font-weight: bold; color: #e91e63;'>{val_mean}</span>
                    </div>
                </div>
            """

        self._template = Template(f"""
            {{% macro html(this, kwargs) %}}
            <div id="stats-dashboard" style="
                position: fixed; 
                bottom: 25px; 
                left: 25px; 
                width: 350px; 
                max-height: 75vh;
                overflow-y: auto;
                background-color: rgba(26, 26, 26, 0.92); 
                color: #ffffff;
                z-index: 9999; 
                padding: 20px; 
                border-radius: 12px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.6);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                border: 1px solid rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="background: #4CAF50; color: black; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 11px; letter-spacing: 0.5px;">ANALYTICS SYSTEM</span>
                    <span style="color: #888; font-size: 11px;">GSD: {resolution_m}m</span>
                </div>
                <h3 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 600; letter-spacing: -0.5px; color: #ffffff;">{index_name} Suite</h3>
                <p style="margin: 0 0 16px 0; font-size: 12px; color: #aaa; line-height: 1.4;">{description}</p>
                
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 12px;">
                    <thead>
                        <tr style="color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                            <th style="text-align: left; padding-bottom: 8px;">Classification Class</th>
                            <th style="text-align: right; padding-bottom: 8px;">Ratio</th>
                            <th style="text-align: right; padding-bottom: 8px;">Area Cover</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                {extra_metrics_html}
            </div>
            {{% endmacro %}}
        """)


class MapVisualizer:
    """
    v1 Visualization Engine for creating standard full-screen single-snapshot maps.
    """
    @staticmethod
    def create_interactive_html(
        matrix: np.ndarray, 
        bbox: tuple, 
        index_name: str, 
        stats_payload: dict, 
        output_filename: str,
        **kwargs
    ) -> str:
        logging.info("Visualizer: Compiling classic v1 viewport display layout framework...")
        target_index = index_name.upper()

        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        folium_bounds = [[min_lat, min_lon], [max_lat, max_lon]]

        interactive_map = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles=None, control_scale=True)
        interactive_map.fit_bounds(folium_bounds)

        interactive_map.get_root().header.add_child(folium.Element(_BASE_DARK_STYLE))
        _add_bounded_tilelayer(interactive_map, "masked-base-pane", folium_bounds)

        style = STYLING_REGISTRY.get(target_index, STYLING_REGISTRY["NDVI"])
        rgba_image = _apply_colormap(matrix, style)

        folium.raster_layers.ImageOverlay(
            image=rgba_image, 
            bounds=folium_bounds, 
            opacity=0.65,
            name=f"Processed {target_index} Layer"
        ).add_to(interactive_map)

        interactive_map.add_child(DashboardOverlay(stats_data=stats_payload))
        folium.LayerControl(collapsed=False).add_to(interactive_map)

        output_dir = "output_maps"
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, output_filename)
        interactive_map.save(html_path)

        return html_path


class TemporalMapVisualizer:
    """
    v2 Layout Visualizer responsible for rendering synchronized side-by-side viewports.
    """
    @staticmethod
    def create_side_by_side_html(
        matrix_pre: np.ndarray,
        matrix_post: np.ndarray,
        bbox: list,
        target_index: str,
        stats_payload: dict,
        output_filename: str
    ) -> str:
        logging.info("Visualizer: Building synchronized dual-window workspace layouts...")
        target_index = target_index.upper()

        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        folium_bounds = [[min_lat, min_lon], [max_lat, max_lon]]

        dual_workspace = plugins.DualMap(location=[center_lat, center_lon], zoom_start=13, tiles=None, control_scale=True)
        dual_workspace.m1.fit_bounds(folium_bounds)
        dual_workspace.m2.fit_bounds(folium_bounds)

        dual_workspace.get_root().header.add_child(folium.Element(_BASE_DARK_STYLE))
        _add_bounded_tilelayer(dual_workspace.m1, "pane-left-clip", folium_bounds)
        _add_bounded_tilelayer(dual_workspace.m2, "pane-right-clip", folium_bounds)

        style = STYLING_REGISTRY.get(target_index, STYLING_REGISTRY["NDVI"])
        rgba_pre  = _apply_colormap(matrix_pre,  style)
        rgba_post = _apply_colormap(matrix_post, style)

        # FIX: z_index completely removed. Let standard Leaflet layers paint natively
        folium.raster_layers.ImageOverlay(
            image=rgba_pre,
            bounds=folium_bounds,
            opacity=0.65,
            name=f"Pre-Event Baseline ({target_index})",
        ).add_to(dual_workspace.m1)

        folium.raster_layers.ImageOverlay(
            image=rgba_post,
            bounds=folium_bounds,
            opacity=0.65,
            name=f"Post-Event Snapshot ({target_index})",
        ).add_to(dual_workspace.m2)

        dual_workspace.add_child(DashboardOverlay(stats_data=stats_payload))
        folium.LayerControl(collapsed=False).add_to(dual_workspace)

        output_dir = "output_maps"
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, output_filename)
        dual_workspace.save(html_path)

        return html_path