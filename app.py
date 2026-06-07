import os
import streamlit as st
import streamlit.components.v1 as components

# ─── IMPORT ENGINE COUPLING ARCHITECTURE ───
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
    DEFAULT_QUERY_TEXT,
    BUFFER_SLIDER_MIN,
    BUFFER_SLIDER_MAX,
    BUFFER_SLIDER_STEP,
    DEFAULT_BUFFER_KM,
)

# ─── STREAMLIT PAGE CONFIGURATION ───
st.set_page_config(
    page_title=APP_PAGE_TITLE,
    page_icon=APP_PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── INFRASTRUCTURE CACHING ───
@st.cache_resource
def bootstrap_eoe_backend():
    """
    Initializes and caches heavy pipeline models in server memory.
    Runs exactly ONCE on boot — keeps subsequent reruns instant.
    """
    geocoder = SpatialGeocoder()
    engine   = SpectralEngine()
    adapter  = Sentinel2Adapter()

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

# Instantiate the cached components
parser, router, executor = bootstrap_eoe_backend()


# ─── MAIN WORKSPACE HEADER ───
st.markdown(
    """
    <div style="background-color: #18181C; padding: 20px; border-radius: 10px; border-left: 5px solid #00FF66; margin-bottom: 25px;">
        <h1 style="color: #00FF66; font-family: monospace; margin: 0; padding-bottom: 5px;">
            🛰️ EARTH OBSERVATION ENGINE v3.0
        </h1>
        <p style="color: #A1A1AA; font-family: monospace; margin: 0; font-size: 14px;">
            Cloud-Native Multi-Spectral Pipeline Workspace Powered by AWS Sentinel-2 Registry
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ─── SIDEBAR CONTROL CENTER ───
with st.sidebar:
    st.markdown("<h3 style='color: #00FF66;'>🎛️ CONTROL CENTER</h3>", unsafe_allow_html=True)
    st.write("Submit standard language commands or fine-tune spatial bounds manually.")
    st.markdown("---")

    user_query = st.text_area(
        "Natural Language Query Request:",
        value=DEFAULT_QUERY_TEXT,
        height=100,
        help="Type a target query specifying an action index, location, and dates."
    )

    st.markdown("<p style='color: #A1A1AA; font-size: 13px; margin-top: 15px;'>🎚️ Manual Parameter Tuning</p>", unsafe_allow_html=True)

    buffer_km = st.slider(
        "Spatial Capture Radius (km)",
        min_value=BUFFER_SLIDER_MIN,
        max_value=BUFFER_SLIDER_MAX,
        value=DEFAULT_BUFFER_KM,
        step=BUFFER_SLIDER_STEP
    )

    st.markdown("---")

    execute_pipeline = st.button("🚀 EXECUTE SAT STREAM", use_container_width=True)


# ─── MAIN WORKSPACE CANVAS ───
if execute_pipeline and user_query:

    with st.spinner("🤖 EOE Chatbot: Booting backend calculations, streaming matrices, and compiling map layout..."):
        try:
            # 1. Feed NLP parser
            request_payload = parser.parse(user_query)

            # 2. Extract pipeline route
            route_packet = router.route(request_payload)

            # 3. Inject manual slider value into the packet
            route_packet["buffer_km"] = float(buffer_km)

            # ─── TELEMETRY DASHBOARD METRICS ───
            st.markdown("<h4 style='color: #A1A1AA; margin-top: 10px;'>📊 Pipeline Telemetry</h4>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Selected Pipeline",     value=route_packet["pipeline"].upper())
            with col2:
                st.metric(label="Target Spectral Index", value=route_packet["index"])
            with col3:
                st.metric(label="Resolved Region Target", value=route_packet["location"].title())

            # 4. Execute pipeline — returns path to generated HTML map
            generated_map_path = executor.execute(route_packet)

            # 5. Read and render map inline
            if os.path.exists(generated_map_path):
                with open(generated_map_path, "r", encoding="utf-8") as html_file:
                    map_markup_content = html_file.read()

                st.markdown("<h4 style='color: #00FF66; margin-top: 20px;'>🗺️ INTERACTIVE MAP WORKSPACE</h4>", unsafe_allow_html=True)
                components.html(map_markup_content, height=APP_MAP_HEIGHT_PX, scrolling=False)
                st.success("🤖 Chatbot: Pipeline run completed successfully! Workspace is live.")
            else:
                st.error("Visualization Defect: Map page compiled but file footprint could not be located on disk.")

        except Exception as pipeline_error:
            st.error(f"❌ Core Execution Failure: {pipeline_error}")

else:
    st.info("👋 Awaiting commands. Enter your telemetry search targets inside the Control Center sidebar and hit Execute!")
