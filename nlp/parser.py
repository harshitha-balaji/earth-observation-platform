import json
import logging
import re
import spacy
import dateparser.search
from datetime import datetime, timedelta
from pathlib import Path

from nlp.location_extractor import LocationExtractor
from config import (
    SPACY_MODEL,
    TEMPORAL_ANCHOR_WORDS,
    INTENT_FALLBACK_MESSAGE,
    LOCATION_FALLBACK_MESSAGE,
)


class QueryParser:
    """
    Parses natural-language Earth Observation queries using spaCy linguistic
    token analysis into structured requests, capturing locations, intents,
    and explicit or natural-language date windows.
    """

    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"

        # Load essential config tracking structures
        self.intents         = self._load_json("intents.json")
        self.response_templates = self._load_json("response_templates.json")

        # ── Single spaCy load ─────────────────────────────────────────────────
        # One model instance shared with LocationExtractor — no double-loading.
        self.nlp = spacy.load(SPACY_MODEL)
        self.location_extractor = LocationExtractor(nlp=self.nlp)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_json(self, filename: str) -> dict:
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Required NLP config file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # ── Public parsing methods ────────────────────────────────────────────────

    def detect_intent(self, query: str) -> dict:
        doc        = self.nlp(query)

        tokens    = [token.text.lower()  for token in doc]
        lemmas    = [token.lemma_.lower() for token in doc]
        full_text = doc.text.lower()

        intent_matches = []

        for intent_name, intent_data in self.intents.items():
            keywords = intent_data.get("keywords", [])
            for keyword in keywords:
                kw_lower = keyword.lower()

                # Multi-word phrase match (e.g. "forest fire")
                if " " in kw_lower and kw_lower in full_text:
                    intent_matches.append((intent_name, intent_data["index"], len(kw_lower)))

                # Single token / lemma match (e.g. "fires" → "fire")
                elif kw_lower in tokens or kw_lower in lemmas:
                    intent_matches.append((intent_name, intent_data["index"], len(kw_lower)))

        if intent_matches:
            # Longest match wins — more specific phrases beat single words
            intent_matches.sort(key=lambda x: x[2], reverse=True)
            return {
                "intent": intent_matches[0][0],
                "index":  intent_matches[0][1],
            }

        raise ValueError(INTENT_FALLBACK_MESSAGE)

    def detect_mode(self, query: str) -> str:
        doc = self.nlp(query.lower())

        # 1. strongest signal: actual dates
        dates = self.extract_dates(query)
        if len(dates) >= 2:
            return "temporal"

        # 2. temporal anchor words fallback
        tokens_and_lemmas = [t.text.lower() for t in doc] + [t.lemma_.lower() for t in doc]

        for word in TEMPORAL_ANCHOR_WORDS:
            if word.lower() in tokens_and_lemmas:
                return "temporal"

        return "snapshot"

    def extract_explicit_dates(self, query: str) -> list:
        """Extracts strict ISO-8601 dates (YYYY-MM-DD) via regex."""
        date_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
        return re.findall(date_pattern, query)

    def extract_dates(self, query: str) -> list:
        """
        Primary date extractor. Tries dateparser first so natural expressions
        like 'last year', 'since 2020', 'past 3 months' are resolved properly.
        Falls back to ISO regex when dateparser finds nothing.
        """
        try:
            results = dateparser.search.search_dates(
                query,
                settings={"PREFER_DAY_OF_MONTH": "first", "RETURN_AS_TIMEZONE_AWARE": False}
            )
            if results:
                # Deduplicate and sort chronologically
                parsed = sorted(
                    {r[1].strftime("%Y-%m-%d") for r in results}
                )
                return parsed
        except Exception:
            pass  # dateparser failed — fall through to regex

        return self.extract_explicit_dates(query)

    def extract_buffer(self, query: str) -> float:
        buffer_pattern = r"\b(\d+(?:\.\d+)?)\s*km\b"
        match = re.search(buffer_pattern, query, re.IGNORECASE)
        if match:
            return float(match.group(1))
        from config import DEFAULT_BUFFER_KM
        return DEFAULT_BUFFER_KM

    def parse(self, query: str) -> dict:
        intent_data = self.detect_intent(query)
        mode        = self.detect_mode(query)
        location    = self.location_extractor.extract(query)

        if not location or not location.strip():
            raise ValueError(LOCATION_FALLBACK_MESSAGE)

        dates     = self.extract_dates(query)
        buffer_km = self.extract_buffer(query)

        pre_window  = None
        post_window = None

        if mode == "temporal" and len(dates) < 2:
            logging.warning(
                "Temporal mode detected but fewer than 2 dates found (%d). "
                "Pipeline will fall back to default date windows from config.",
                len(dates)
            )

        if len(dates) >= 2:
            d1 = datetime.strptime(dates[0],  "%Y-%m-%d")
            d2 = datetime.strptime(dates[-1], "%Y-%m-%d")
            delta_days = (d2 - d1).days

            if delta_days <= 0:
                raise ValueError(
                    "Chronological Error: The first query date must precede the final boundary target date."
                )

            mid_date_obj = d1 + timedelta(days=delta_days // 2)
            mid_date     = mid_date_obj.strftime("%Y-%m-%d")

            pre_window  = f"{dates[0]}/{mid_date}"
            post_window = f"{mid_date}/{dates[-1]}"

        return {
            "intent":     intent_data["intent"],
            "index":      intent_data["index"],
            "mode":       mode,
            "location":   location.strip(),
            "buffer_km":  buffer_km,
            "pre_window": pre_window,
            "post_window": post_window,
        }
