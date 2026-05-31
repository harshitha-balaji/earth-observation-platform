# 🛰️ Earth Observation Engine
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
[![pystac-client](https://img.shields.io/badge/STAC-pystac--client-1a73e8?style=flat-square)](https://pystac-client.readthedocs.io/)
[![odc-stac](https://img.shields.io/badge/Raster-odc--stac-2e7d32?style=flat-square)](https://odc-stac.readthedocs.io/)
[![Folium](https://img.shields.io/badge/Maps-Folium-77b829?style=flat-square)](https://python-visualization.github.io/folium/)
[![NumPy](https://img.shields.io/badge/Math-NumPy-013243?style=flat-square&logo=numpy&logoColor=white)](https://numpy.org/)
[![geopy](https://img.shields.io/badge/Geocoding-geopy-e65100?style=flat-square)](https://geopy.readthedocs.io/)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

> **Multi-spectral satellite analysis pipeline** — stream real Sentinel-2 imagery from space, compute spectral indices, and render live interactive maps. All from the terminal.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Sentinel-2](https://img.shields.io/badge/Sentinel--2-L2A-1a73e8?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)

---

## What is this?

This pipeline connects directly to the **AWS Earth Search STAC catalog** and streams real, cloud-optimized Sentinel-2 satellite imagery over any location on Earth — no manual downloads, no accounts, no dataset prep.

Type a place name. Get a live spectral analysis map in your browser.

```
Enter location name: Lake Mead
Select index: NDWI
→ Resolving coordinates via Nominatim...
→ Querying Sentinel-2 L2A catalog...
→ Streaming cloud-native pixel window...
→ Computing normalized difference matrix...
→ Rendering interactive map → opening browser
```

---

## Features

### v1 — Single Snapshot Mode
- Geocode any location by plain text (powered by OpenStreetMap Nominatim)
- Stream Sentinel-2 L2A bands directly from AWS STAC (no download required)
- Compute spectral indices on the raw pixel matrix
- Render a full-screen interactive Folium/Leaflet map with a stats dashboard overlay
- Spatial statistics: coverage breakdown by class, area in km², matrix min/max/mean

### v2 — Multi-Temporal Change Detection Mode
- Dual STAC queries across two separate date windows (pre/post event)
- Pixel-aligned differential matrix (Δindex = pre − post) at fixed resolution
- Synchronized side-by-side split-map view for direct visual comparison
- Change classification: severe disturbance → stable → active regrowth

---

## Supported Spectral Indices

| Index | What it measures | Bands used |
|-------|-----------------|------------|
| **NDVI** | Live green vegetation density | NIR, Red |
| **NDWI** | Open water bodies & flood extent | Green, NIR |
| **NDBI** | Urban infrastructure & concrete | SWIR, NIR |
| **NBR**  | Wildfire burn severity | NIR, SWIR2 |
| **NDSI** | Snow and glacial ice cover | Green, SWIR |

All indices are config-driven via `recipes.json` — adding a new one requires zero changes to the core engine.

---

## Tech Stack

| Layer | Library |
|-------|---------|
| STAC Catalog Access | `pystac-client` |
| Cloud-native raster streaming | `odc-stac` |
| Numerical matrix math | `numpy` |
| Geocoding | `geopy` (Nominatim) |
| Map rendering | `folium` + `branca` |
| Colormap rendering | `matplotlib` |

---

## Getting Started

### 1. Install dependencies

```bash
pip install pystac-client odc-stac numpy geopy folium branca matplotlib
```

### 2. Clone and run

```bash
git clone https://github.com/YOUR_USERNAME/earth-observation-engine.git
cd earth-observation-engine
python main.py
```

### 3. Follow the prompts

```
Select Operational Pipeline Mode:
  [1] Baseline Snapshot Exploration (v1 Core)
  [2] Multi-Temporal Side-by-Side Comparison (v2 Engine)

Enter location name: Aral Sea
Select Research Window Scale: 3 (20km x 20km)
Select Spectral Analysis Index: 2 (NDWI)
```

An interactive HTML map opens automatically in your browser. Output files are saved to `output_maps/`.

---

## Project Structure

```
spectral_pipeline/
├── main.py              # CLI entry point & pipeline router
├── geocoder.py          # Text → bounding box (Nominatim)
├── adapter.py           # STAC streaming layer (abstract + Sentinel-2 concrete)
├── engine.py            # Spectral math engine (normalized difference core)
├── temporal_engine.py   # Dual-date change detection pipeline (v2)
├── visualizer.py        # Folium map builders + dashboard overlay
└── recipes.json         # Index configs: bands, classes, resolution
```

The architecture is deliberately layered — `engine.py` never touches maps, `visualizer.py` never touches satellite data. Each component can be swapped independently.

---

## Example Use Cases

| Scenario | Mode | Index |
|----------|------|-------|
| Track reservoir shrinkage over time | v2 (temporal) | NDWI |
| Map post-wildfire burn scar extent | v2 (temporal) | NBR |
| Monitor urban expansion on city outskirts | v2 (temporal) | NDBI |
| Quick vegetation health snapshot | v1 (single) | NDVI |
| Glacier retreat monitoring | v2 (temporal) | NDSI |

---

## Roadmap

- [ ] `requirements.txt` and `pyproject.toml`
- [ ] Landsat-8/9 adapter (extend `SatelliteAdapter`)
- [ ] Web UI front-end (replace terminal prompts)
- [ ] Export to GeoTIFF
- [ ] Cloud cover threshold as user parameter
- [ ] Batch processing for multiple locations

---

## Notes

- Imagery is sourced from the [AWS Earth Search](https://earth-search.aws.element84.com/v1) public STAC endpoint. No API key required.
- Scenes are filtered to **< 5% cloud cover** and sorted by cloud coverage automatically.
- Temporal mode uses **EPSG:3857** (Web Mercator) with pinned resolution to guarantee pixel-aligned arrays across date windows — critical for valid delta computation.

---

*Built as a personal project to explore remote sensing and satellite data pipelines.*
