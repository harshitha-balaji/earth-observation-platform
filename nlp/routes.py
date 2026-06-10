from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import logging
from config import (
    DEFAULT_BUFFER_KM,
    TEMPORAL_PRE_WINDOW_DEFAULT,
    TEMPORAL_POST_WINDOW_DEFAULT,
)

@dataclass
class BaseRoute:
    """
    Abstract structural base defining parameters common to every transaction
    on the Earth Observation Platform.
    """
    location: str
    index: str
    buffer_km: float = DEFAULT_BUFFER_KM

    def __post_init__(self) -> None:
        # Enforce uppercase matrix index targets
        self.index = self.index.upper()
        
        # Clean background noise from location inputs
        if self.location:
            cleaned = self.location.strip()
            # Remove leading grammatical spatial prepositions if present
            for noise_prefix in ["in ", "near ", "around ", "across ", "over "]:
                if cleaned.lower().startswith(noise_prefix):
                    cleaned = cleaned[len(noise_prefix):].strip()
            self.location = cleaned.title()


@dataclass
class SnapshotRoute(BaseRoute):
    """
    Isolates single-scene observation parameters over a target region.
    Guarantees no multi-temporal date window overlaps are processed.
    """
    pipeline: str = field(default="snapshot", init=False)


@dataclass
class TemporalRoute(BaseRoute):
    """
    Models tracking requirements for dual-date timeline change metrics.
    Automatically formats temporal spans or transparently implements system defaults.
    """
    pipeline: str = field(default="temporal", init=False)
    pre_window: Optional[str] = None
    post_window: Optional[str] = None

    def __post_init__(self) -> None:
        # Call foundational location and index normalization logic first
        super().__post_init__()

        # Transparently fallback to standard system timelines if the parser missed targets
        if not self.pre_window:
            self.pre_window = TEMPORAL_PRE_WINDOW_DEFAULT
        if not self.post_window:
            self.post_window = TEMPORAL_POST_WINDOW_DEFAULT

        # Chronological Invariant Protection: Validate window boundaries
        try:
            # Unpack first window start, and last window end bounds
            start_date_str = self.pre_window.split("/")[0]
            end_date_str = self.post_window.split("/")[-1]
            
            d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
            d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if (d2 - d1).days <= 0:
                raise ValueError(
                    "Chronological Error: The first tracking boundary must precede the final target date."
                )
        except (ValueError, IndexError) as err:
            logging.error("Failed to parse or validate chronological windows: %s", err)
            raise ValueError(f"Invalid timeline boundaries specified: {err}")