# ─── EOE v3.0 — Central Configuration ───
# All hardcoded values live here. Edit this file to tune the platform.

# ── Geocoder ──────────────────────────────────────────────────────────────────
GEOCODER_USER_AGENT       = "satellite_pipeline_explorer"
GEOCODER_TIMEOUT_SECONDS  = 10
KM_PER_DEGREE_LATITUDE    = 111.0
BBOX_COORDINATE_PRECISION = 4        # decimal places for rounding bbox coords

# ── Spatial defaults ──────────────────────────────────────────────────────────
DEFAULT_BUFFER_KM         = 5.0
BUFFER_SLIDER_MIN         = 1.0
BUFFER_SLIDER_MAX         = 25.0
BUFFER_SLIDER_STEP        = 0.5

# ── Sentinel-2 adapter ────────────────────────────────────────────────────────
STAC_ENDPOINT             = "https://earth-search.aws.element84.com/v1"
STAC_COLLECTION           = "sentinel-2-l2a"
MAX_CLOUD_COVER_PCT       = 5        # scenes with cloud cover above this are rejected
DEFAULT_TIME_WINDOW       = "2026-01-01/2026-06-01"

# ── Temporal pipeline defaults (fallback when user gives no dates) ─────────────
TEMPORAL_PRE_WINDOW_DEFAULT  = "2025-01-01/2025-06-01"
TEMPORAL_POST_WINDOW_DEFAULT = "2026-01-01/2026-06-01"

# ── NLP parser ────────────────────────────────────────────────────────────────
SPACY_MODEL               = "en_core_web_sm"
DEFAULT_INTENT_CONFIDENCE = 0.0      # placeholder until confidence scoring added in v3.1
INTENT_FALLBACK_MESSAGE   = (
    "Could not determine analysis intent from query. "
    "(Try naming an index like NDVI, NBR, NDWI, NDBI, or NDSI!)"
)
LOCATION_FALLBACK_MESSAGE = (
    "Could not extract a valid location from your prompt. "
    "Please explicitly define a city or tracking region."
)

# ── Temporal mode trigger keywords ────────────────────────────────────────────
TEMPORAL_ANCHOR_WORDS = [
    "between", "over", "history", "trend", "temporal",
    "years", "months", "timeline", "delta", "change",
    "before", "after", "since", "compare", "shift"
]

# ── Location extractor ────────────────────────────────────────────────────────
LOCATION_ENTITY_LABELS    = ["GPE", "LOC"]
LOCATION_NOISE_WORDS      = ["Using", "Between", "From", "With", "On"]

# ── Temporal change engine classification bins ────────────────────────────────
TEMPORAL_CHANGE_BINS = [
    {"label": "Severe Disturbance / Environmental Loss", "min":  0.25, "max":  2.0 },
    {"label": "Moderate Loss / Localized Shift",         "min":  0.10, "max":  0.25},
    {"label": "Stable / Unchanged Surface Conditions",   "min": -0.10, "max":  0.10},
    {"label": "Active Growth / Moisture Rebound",        "min": -2.0,  "max": -0.10},
]

# ── Streamlit UI ──────────────────────────────────────────────────────────────
APP_PAGE_TITLE            = "EOE v3.0 | Earth Observation Dashboard"
APP_PAGE_ICON             = "🛰️"
APP_MAP_HEIGHT_PX         = 650
DEFAULT_QUERY_TEXT        = "Track forest fires in California between 2026-01-01 and 2026-05-01"
