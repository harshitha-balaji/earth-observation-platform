# 🛰️ Earth Observation Platform (EOP) v4.0

[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/harshithabalaji/earth-observation-platform)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Sentinel-2](https://img.shields.io/badge/Sentinel--2-AWS%20STAC-orange?style=flat-square)](https://earth-search.aws.element84.com/v1)
![spaCy](https://img.shields.io/badge/NLP-spaCy-09A3D5?style=flat-square&logo=spacy&logoColor=white)
![sklearn](https://img.shields.io/badge/CV-scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)
![Config](https://img.shields.io/badge/architecture-config--driven-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## What is this?

GIS tools require GIS expertise. EOP doesn't.

Describe what you want to analyze in plain English — a location, a phenomenon, a date range — and the platform handles everything else: parsing intent, streaming real Sentinel-2 L2A imagery from AWS, computing spectral indices on the raw pixel matrix, and classifying change using unsupervised K-Means clustering. No downloads. No accounts. No GIS experience required.

```
Track forest fires in California between 2025-06-01 and 2026-01-01
→ Parsing natural language query...
→ Intent detected: NBR (Burn Severity) | Mode: temporal
→ Location resolved: California [-124.48, 32.53, -114.13, 42.01]
→ Querying Sentinel-2 L2A STAC catalog (pre-event window)...
→ Querying Sentinel-2 L2A STAC catalog (post-event window)...
→ Computing dNBR differential matrix...
→ Running K-Means CV segmentation on change matrix...
→ Clusters converged — rendering synchronized dual-map workspace
```

---

## What it's useful for

Environmental monitoring, land cover analysis, disaster impact assessment, urban growth tracking, agricultural health monitoring, glacier and water body change detection — any domain where satellite-derived spectral intelligence matters. The natural language interface makes it accessible to domain experts who don't want to write GIS code, while the modular architecture makes it extensible for engineers who do.

---

## Version Roadmap

EOP evolved across four versions, each adding a distinct capability layer:

### v1 — Spectral Core
The foundation. A terminal-based pipeline that geocoded a location by name, streamed Sentinel-2 bands from AWS STAC, computed a spectral index on the raw pixel matrix, and rendered a full-screen interactive Folium map with a dark-themed analytics dashboard overlay. Single snapshot mode only.

### v2 — Temporal Intelligence
Added multi-temporal change detection. Dual STAC queries across two separate date windows, pixel-aligned differential matrix computation (Δindex = pre − post) at fixed resolution, and a synchronized side-by-side split-map for direct visual comparison. Introduced change classification with severity tiers.

### v3 — Natural Language Platform
Replaced the terminal menu entirely with a Streamlit web workspace and NLP control center. spaCy NER for geographic entity extraction, intent classification via phrase-length keyword matching, `dateparser` integration for natural language date expressions, and automatic temporal vs snapshot mode detection. Centralized `config.py` architecture and `@st.cache_resource` backend caching.

### v4 — CV Intelligence Layer *(current)*
Added an unsupervised computer vision classification layer and overhauled the UI. K-Means clustering replaces hardcoded threshold bins — change boundaries are now learned from the data itself. Dataclass-based pipeline contracts replace loose dictionaries between NLP and execution layers. Redesigned mission-log UI with Plotly distribution charts and in-memory HTML rendering.

---

## Features

### NLP Control Center
Write queries the way you'd describe them to a colleague:
- `"Show vegetation health in the Amazon basin"`
- `"Track urban expansion in Bangalore between 2024-01-01 and 2026-01-01"`
- `"Map flood extent in Kerala after the 2018-08-01 monsoon"`
- `"How did the Himalayan snow cover change between 2023-01-01 and 2025-12-01"`

The NLP layer handles intent classification, location entity extraction, temporal vs snapshot mode detection, and date window parsing — including natural expressions like "last year" and "since 2020." A regex fallback handles natural landmarks that spaCy NER misses.

### K-Means CV Classification Layer
Change matrices are segmented using scikit-learn K-Means clustering rather than fixed thresholds. Centroids are sorted post-convergence to guarantee ordered semantic labels (Label 0 = max loss → Label 3 = max growth) regardless of how the clusters initialize. Boundaries adapt to the actual data distribution of each unique analysis — a fire in a dry region and a fire in a dense forest produce different cluster boundaries, as they should.

### Interactive Map Workspace
Full-screen Folium maps with dark CartoDB basemap, per-index matplotlib colormaps (YlGn for NDVI, PuRd for NBR etc.), and an embedded analytics dashboard showing classification breakdown, area coverage, and matrix intensity statistics. Temporal mode renders a synchronized side-by-side DualMap for direct pre/post visual comparison.

### Mission Log
Sidebar tracks the last 5 analyses with timestamp, location, pipeline type, and index — persistent across reruns via Streamlit session state.

### Distribution Chart
Plotly horizontal bar chart visualizes class distribution per analysis run with dynamic titles ("Temporal Change Distribution" vs "Land Cover Distribution") based on pipeline context.

---

## Supported Spectral Indices

| Index | What it measures | Bands used | Resolution |
|-------|-----------------|------------|------------|
| NDVI | Live green vegetation density | NIR, Red | 10m |
| NDWI | Open water bodies & flood extent | Green, NIR | 10m |
| NDBI | Urban infrastructure & concrete | SWIR, NIR | 20m |
| NBR | Wildfire burn severity | NIR, SWIR2 | 20m |
| NDSI | Snow and glacial ice cover | Green, SWIR | 20m |

All indices are config-driven via `recipes.json` — adding a new one requires zero changes to the core engine.

---

## Tech Stack

| Layer | Library |
|-------|---------|
| Web frontend | `Streamlit` |
| NLP parsing | `spaCy` (en_core_web_sm) + `dateparser` |
| CV classification | `scikit-learn` (K-Means) |
| STAC catalog access | `pystac-client` |
| Cloud-native raster streaming | `odc-stac` |
| Numerical matrix math | `numpy` |
| Geocoding | `geopy` (Nominatim) |
| Map rendering & charts | `folium`, `branca`, `plotly`, `matplotlib` |

---

## Getting Started

### 1. Install dependencies
```bash
pip install streamlit pystac-client odc-stac numpy geopy folium branca matplotlib spacy dateparser scikit-learn plotly pandas
python -m spacy download en_core_web_sm
```

### 2. Clone and run
```bash
git clone https://github.com/harshitha-balaji/earth-observation-engine.git
cd earth-observation-engine
streamlit run app.py
```

### 3. Use the platform
Type a natural language query in the main input and hit **Analyze**. Adjust the buffer radius in the sidebar for larger or smaller capture windows.

```
vegetation in Bengaluru
track fire damage in California between 2025-01-01 and 2026-01-01
flood extent near Chennai after 2018-08-01 to 2018-10-01
```

---

## Project Structure

```
├── app.py                          # Streamlit frontend & pipeline orchestrator
├── config.py                       # Central configuration — all constants live here
├── nlp/
│   ├── parser.py                   # NLP core: intent, location, date, mode extraction
│   ├── router.py                   # Routes parsed payload → typed dataclass routes
│   ├── routes.py                   # SnapshotRoute & TemporalRoute dataclass contracts
│   ├── location_extractor.py       # spaCy NER-based geographic entity extractor
│   └── config/
│       ├── intents.json            # Intent → spectral index keyword mapping
│       ├── aliases.json            # Query normalization / shorthand expansion
│       └── response_templates.json # UI feedback text baselines
│
├── spectral_pipeline/
│   ├── geocoder.py                 # Text → bounding box (Nominatim)
│   ├── adapter.py                  # STAC streaming layer (abstract + Sentinel-2 concrete)
│   ├── engine.py                   # Spectral math engine (normalized difference core)
│   ├── temporal_engine.py          # Dual-date change detection pipeline
│   ├── visualizer.py               # Folium map builders + analytics dashboard overlay
│   └── recipes.json                # Index configs: bands, colormaps, resolution
├── cv/
│   └── kmeans_classifier.py        # Unsupervised K-Means CV change classification layer
└── interface/
    └── command_executor.py         # Execution coordinator: geocode → stream → compute → render
```

The architecture is deliberately layered — `engine.py` never touches maps, `visualizer.py` never touches satellite data, `parser.py` knows nothing about spectral indices, and `cv/` is isolated from both the data pipeline and the UI. Each component can be swapped or extended independently.

---

## Design Decisions

**Why config-driven indices?** `recipes.json` binds band mappings, colormaps, and resolution to each index name. The engine executes a normalized difference formula — the config determines which bands to use. Adding a new index is a JSON edit, not a code change.

**Why K-Means over hardcoded bins?** Fixed thresholds assume the same change boundaries apply to every location, season, and index. K-Means finds natural cluster boundaries in the actual data distribution. A burn scar in the Atacama and a burn scar in the Amazon rainforest have different baseline NDVI values — their change classification should reflect that.

**Why dataclasses over dictionaries?** `SnapshotRoute` and `TemporalRoute` guarantee type safety and field presence between the NLP layer and the execution layer. Validation and normalization (title-casing locations, uppercasing index names, chronological date checks) happen at construction time in `__post_init__`, not scattered across the pipeline.

---

## Notes

- Imagery sourced from the [AWS Earth Search](https://earth-search.aws.element84.com/v1) public STAC endpoint — no API key required
- Scenes filtered to `< 5%` cloud cover automatically
- Temporal mode uses EPSG:3857 (Web Mercator) with pinned resolution to guarantee pixel-aligned arrays across date windows — critical for valid delta computation
- Backend models and pipeline components cached on first boot via `@st.cache_resource` — subsequent reruns are instant
- K-Means centroids sorted post-convergence so semantic cluster labels are consistent across every run

---

## Limitations

- NLP intent classification uses keyword matching — ambiguous or highly domain-specific queries may misroute
- Geocoding depends on Nominatim's coverage — obscure or informal location names may fail to resolve
- Cloud cover filter (`< 5%`) can reduce available scenes in persistently cloudy regions
- K-Means cluster count is fixed at 4 — unusual data distributions may not segment cleanly into four meaningful classes
- Temporal alignment assumes consistent scene geometry across dates — significant orbital variation may affect delta accuracy

---

*Built at the intersection of NLP, remote sensing, and unsupervised ML — because satellite data shouldn't require a GIS degree to use.*
