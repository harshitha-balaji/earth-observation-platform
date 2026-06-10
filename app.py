import os
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pandas as pd
import plotly.express as px

from spectral_pipeline.geocoder import SpatialGeocoder
from spectral_pipeline.engine import SpectralEngine
from spectral_pipeline.adapter import Sentinel2Adapter
from spectral_pipeline.temporal_engine import TemporalChangeEngine

from nlp.parser import QueryParser
from nlp.router import QueryRouter
from interface.command_executor import CommandExecutor

from config import (
    APP_PAGE_TITLE,
    APP_PAGE_ICON,
    APP_MAP_HEIGHT_PX,
    BUFFER_SLIDER_MIN,
    BUFFER_SLIDER_MAX,
    BUFFER_SLIDER_STEP,
    DEFAULT_BUFFER_KM,
)

# ─────────────────────────────
# THEME
# ─────────────────────────────
PRIMARY = "#4F8CFF"
PANEL = "#18181C"
TEXT = "#FFFFFF"
MUTED = "#A1A1AA"

# ─────────────────────────────
# PAGE CONFIG
# ─────────────────────────────
st.set_page_config(
    page_title=APP_PAGE_TITLE,
    page_icon=APP_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────
# STATE
# ─────────────────────────────
if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "has_run" not in st.session_state:
    st.session_state.has_run = False

# ─────────────────────────────
# BACKEND BOOTSTRAP
# ─────────────────────────────
@st.cache_resource
def bootstrap_eop_backend():
    geocoder = SpatialGeocoder()
    engine = SpectralEngine()
    adapter = Sentinel2Adapter()

    temporal_engine = TemporalChangeEngine(
        geocoder=geocoder,
        adapter=adapter,
        spectral_engine=engine
    )

    parser = QueryParser()
    router = QueryRouter()

    executor = CommandExecutor(
        geocoder=geocoder,
        adapter=adapter,
        engine=engine,
        temporal_engine=temporal_engine
    )

    return parser, router, executor


parser, router, executor = bootstrap_eop_backend()

# ─────────────────────────────
# LANDING PAGE
# ─────────────────────────────
st.markdown(f"""
<div style="
    background-color:{PANEL};
    padding: 28px;
    border-radius: 14px;
    border-left: 6px solid {PRIMARY};
    margin-bottom: 20px;
">
    <h1 style="color:{PRIMARY}; margin:0;">
        🛰 Earth Observation Platform
    </h1>
    <p style="color:{MUTED}; margin-top:10px; font-size:15px;">
        Welcome back.<br><br>
        Explore vegetation, urban growth, water bodies,<br>
        and environmental change using satellite imagery<br>
        and natural language.
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────
# MAIN INPUT (UPDATED UI)
# ─────────────────────────────
with st.container():
    st.markdown(
        "<p style='color:#A1A1AA; font-size:13px;'>Natural Language Query</p>",
        unsafe_allow_html=True
    )

    user_query = st.text_input(
        "",
        placeholder="Track forest fires in California between 2025-01-01 and 2026-01-01",
        label_visibility="collapsed"
    )

    execute_pipeline = st.button("🛰 Analyze", use_container_width=True)

# ─────────────────────────────
# SIDEBAR — MISSION CONTROL
# ─────────────────────────────
with st.sidebar:
    st.markdown("## 🎛 Mission Control")

    st.markdown("### 📜 Mission Log")

    for item in reversed(st.session_state.query_history[-5:]):
        st.markdown(f"**{item['time']}**  \n{item['loc']} — {item['pipe']}")

    st.markdown("---")
    st.markdown("### ⚙ Advanced Parameters")

    buffer_km = st.slider(
        "Buffer Radius (km)",
        min_value=BUFFER_SLIDER_MIN,
        max_value=BUFFER_SLIDER_MAX,
        value=DEFAULT_BUFFER_KM,
        step=BUFFER_SLIDER_STEP
    )

# ─────────────────────────────
# EXECUTION FLOW
# ─────────────────────────────
if execute_pipeline and user_query:

    st.session_state.has_run = True

    with st.spinner(f"Analyzing {user_query} ..."):
        try:
            request_payload = parser.parse(user_query)
            route_packet = router.route(request_payload)

            route_packet.buffer_km = float(buffer_km)

            result = executor.execute(route_packet)

            map_path = result["map_path"]
            stats_payload = result["stats_payload"]
            metadata = result["metadata"]

            # ─────────────────────────────
            # MAP
            # ─────────────────────────────
            st.markdown("## 🗺 Analysis Result")

            st.markdown(f"""
            <div style="
                background:{PANEL};
                padding:10px;
                border-radius:10px;
                border-left:4px solid {PRIMARY};
                margin-bottom:10px;
                color:{TEXT};
            ">
            📍 {route_packet.location}  
            🛰 {route_packet.index} Analysis  
            </div>
            """, unsafe_allow_html=True)

            if os.path.exists(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    map_html = f.read()

                components.html(map_html, height=APP_MAP_HEIGHT_PX, scrolling=False)

            else:
                st.error("Map could not be loaded.")

            # ─────────────────────────────
            # 📊 MISSION INSIGHTS
            # ─────────────────────────────
            st.markdown("## 📊 Mission Insights")

            summary = stats_payload.get("summary_metrics", {})

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Min", summary.get("min", "N/A"))
            col2.metric("Max", summary.get("max", "N/A"))
            col3.metric("Mean", summary.get("mean", "N/A"))
            col4.metric("Resolution", stats_payload.get("resolution_m", "N/A"))

            # ─────────────────────────────
            # 🌍 DYNAMIC DISTRIBUTION TITLE
            # ─────────────────────────────
            pipeline_type = route_packet.pipeline.lower() if hasattr(route_packet, "pipeline") else "snapshot"

            if pipeline_type == "temporal":
                chart_title = "## 📈 Temporal Change Distribution"
            else:
                chart_title = "## 🌍 Land Cover Distribution"

            st.markdown(chart_title)

            classes = stats_payload.get("class_distribution", [])

            if classes:
                df = pd.DataFrame({
                    "Class": [c["label"] for c in classes],
                    "Percentage": [c["percentage"] for c in classes]
                })

                fig = px.bar(
                    df,
                    x="Percentage",
                    y="Class",
                    orientation="h",
                    text="Percentage"
                )

                fig.update_layout(
                    plot_bgcolor=PANEL,
                    paper_bgcolor=PANEL,
                    font_color=TEXT,
                    height=350
                )

                st.plotly_chart(fig, use_container_width=True)

            # ─────────────────────────────
            # HISTORY
            # ─────────────────────────────
            st.session_state.query_history.append({
                "time": datetime.now().strftime("%H:%M"),
                "loc": route_packet.location,
                "pipe": route_packet.pipeline.upper(),
                "index": route_packet.index
            })

        except Exception as e:
            st.error(f"Analysis failed: {e}")

else:
    st.info("Welcome back. What would you like to analyze today?")