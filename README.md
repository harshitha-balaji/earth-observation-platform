# 🛰️ Earth Observation Platform v3.0

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white)
![Sentinel-2](https://img.shields.io/badge/Sentinel--2-AWS%20STAC-orange)
![spaCy](https://img.shields.io/badge/NLP-spaCy-09A3D5?logo=spacy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Cloud-native multi-spectral satellite analysis platform — stream real Sentinel-2 imagery from AWS, describe what you want to analyze in plain English, and get a live interactive map in your browser.

No downloads. No accounts. No GIS experience required.

```
Track forest fires in California between 2025-06-01 and 2026-01-01
→ Parsing natural language query...
→ Intent detected: NBR (Burn Severity) | Mode: temporal
→ Location resolved: California [-124.48, 32.53, -114.13, 42.01]
→ Querying Sentinel-2 L2A STAC catalog (pre-event window)...
→ Querying Sentinel-2 L2A STAC catalog (post-event window)...
→ Computing dNBR differential matrix...
→ Rendering synchronized split-map workspace → live in browser
```

---

## What is this?

EOP v3.0 upgrades the original terminal-based pipeline into a full **Streamlit web workspace** with a natural language control center. Instead of navigating menus, you describe your analysis in plain English — the NLP engine extracts the intent, location, spectral target, and date window automatically and routes it through the correct pipeline.

The satellite data pipeline underneath is unchanged: direct AWS Earth Search STAC catalog access, cloud-optimized GeoTIFF streaming, and pixel-level spectral math — all without any manual data downloads.

---

## What's New in v3.0

| Feature | v2 (CLI) | v3.0 (Platform) |
|---|---|---|
| Interface | Terminal menu prompts | Streamlit web workspace |
| Query input | Menu selections | Natural language text |
| NLP engine | None | spaCy NER + intent classifier |
| Date parsing | ISO input only | Natural expressions + ISO dates |
| Location extraction | Plain text input | Automatic entity extraction |
| Pipeline routing | Manual mode selection | Auto-detected from query |
| Config management | Scattered constants | Centralized `config.py` |
| Backend caching | None | `@st.cache_resource` (one-time boot) |

---

## Features

### NLP Control Center
Write queries the way you'd describe them to a colleague:
- `"Show vegetation health in the Amazon basin"`
- `"Track urban expansion in Bangalore between 2024-01-01 and 2026-01-01"`
- `"Map flood extent in Kerala after the 2018-08-01 monsoon"`
- `"How did the Himalayan glaciers change since 2023-01-01 to 2025-12-01"`

The NLP layer handles intent classification, location entity extraction, temporal vs snapshot mode detection, and date window parsing — including natural expressions like "last year" and "since 2020."

### v1 — Single Snapshot Mode
- Geocode any location by name via OpenStreetMap Nominatim
- Stream Sentinel-2 L2A bands directly from AWS STAC
- Compute spectral indices on the raw pixel matrix
- Render a full-screen interactive Folium/Leaflet map with stats dashboard overlay
- Spatial statistics: coverage breakdown by class, area in km², matrix min/max/mean

### v2 — Multi-Temporal Change Detection Mode
- Dual STAC queries across two date windows (pre/post event)
- Pixel-aligned differential matrix (Δindex = pre − post) at fixed resolution
- Synchronized side-by-side split-map for direct visual comparison
- Change classification: severe disturbance → stable → active regrowth

### v3 — Natural Language Platform
- Plain English query interface replacing all terminal prompts
- Automatic intent, location, date, and mode extraction
- Centralized config architecture for all operational parameters
- Streamlit web workspace with telemetry dashboard

---

## Supported Spectral Indices

| Index | What it measures | Bands used | Resolution |
|---|---|---|---|
| NDVI | Live green vegetation density | NIR, Red | 10m |
| NDWI | Open water bodies & flood extent | Green, NIR | 10m |
| NDBI | Urban infrastructure & concrete | SWIR, NIR | 20m |
| NBR | Wildfire burn severity | NIR, SWIR2 | 20m |
| NDSI | Snow and glacial ice cover | Green, SWIR | 20m |

All indices are config-driven via `recipes.json` — adding a new one requires zero changes to the core engine.

---

## Tech Stack

| Layer | Library |
|---|---|
| Web frontend | Streamlit |
| NLP parsing | spaCy (`en_core_web_sm`) + dateparser |
| STAC catalog access | pystac-client |
| Cloud-native raster streaming | odc-stac |
| Numerical matrix math | numpy |
| Geocoding | geopy (Nominatim) |
| Map rendering | folium + branca |
| Colormap rendering | matplotlib |

---

## Getting Started

### 1. Install dependencies
```bash
pip install streamlit pystac-client odc-stac numpy geopy folium branca matplotlib spacy dateparser
python -m spacy download en_core_web_sm
```

### 2. Clone and run
```bash
git clone https://github.com/harshitha-balaji/earth-observation-engine.git
cd earth-observation-engine
streamlit run app.py
```

### 3. Use the Control Center
Enter a natural language query in the sidebar, adjust the spatial capture radius if needed, and hit **EXECUTE SAT STREAM**.

```
Track forest fires in California between 2025-06-01 and 2026-01-01
```

The interactive map renders live in the workspace canvas. Output HTML files are saved to `output_maps/`.

---

## Project Structure

```
├── app.py                          # Streamlit frontend & pipeline orchestrator
├── config.py                       # Central configuration — all constants live here
├── nlp/
│   ├── parser.py                   # NLP core: intent, location, date, mode extraction
│   ├── router.py                   # Routes parsed payload to snapshot or temporal pipeline
│   ├── location_extractor.py       # spaCy NER-based geographic entity extractor
│   └── config/
│       ├── intents.json            # Intent → spectral index keyword mapping
│       ├── aliases.json            # Query normalization / shorthand expansion
│       ├── temporal_keywords.json  # Tokens that trigger temporal mode detection
│       └── response_templates.json # UI feedback text baselines
├── spectral_pipeline/
│   ├── geocoder.py                 # Text → bounding box (Nominatim)
│   ├── adapter.py                  # STAC streaming layer (abstract + Sentinel-2 concrete)
│   ├── engine.py                   # Spectral math engine (normalized difference core)
│   ├── temporal_engine.py          # Dual-date change detection pipeline
│   ├── visualizer.py               # Folium map builders + dashboard overlay
│   └── recipes.json                # Index configs: bands, classes, resolution
└── interface/
    └── command_executor.py         # Execution coordinator: geocode → stream → compute → render
```

The architecture is deliberately layered — `engine.py` never touches maps, `visualizer.py` never touches satellite data, `parser.py` knows nothing about spectral indices. Each component can be swapped or extended independently.

---

## Roadmap

- [ ] K-means data-driven change classification (v4)
- [ ] Dataclass-based pipeline payload contracts (v4)
- [ ] PDF report generation per analysis (v4)
- [ ] Landsat-8/9 adapter (extend `SatelliteAdapter`)

---

## Notes

- Imagery is sourced from the [AWS Earth Search](https://earth-search.aws.element84.com/v1) public STAC endpoint. No API key required.
- Scenes are filtered to `< 5%` cloud cover and sorted by cloud coverage automatically.
- Temporal mode uses EPSG:3857 (Web Mercator) with pinned resolution to guarantee pixel-aligned arrays across date windows — critical for valid delta computation.
- The NLP layer uses spaCy NER for location extraction with a regex fallback for natural landmarks. Date parsing uses `dateparser` with ISO-8601 regex fallback.
- Backend models and pipeline components are cached on first boot via `@st.cache_resource` — subsequent reruns are instant.

---

Built to explore the intersection of NLP, remote sensing, and satellite data pipelines.
