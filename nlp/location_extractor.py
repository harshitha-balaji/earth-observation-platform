import re
import spacy

from config import LOCATION_ENTITY_LABELS, LOCATION_NOISE_WORDS


class LocationExtractor:
    """
    Leverages spaCy Named Entity Recognition (NER) to contextually
    extract geographical locations and regions from query text, with an
    adaptive regex fallback for natural landmarks and mountain peaks.

    Accepts a shared spaCy Language instance to avoid loading the model
    twice when QueryParser already holds one.
    """

    def __init__(self, nlp: spacy.Language = None):
        # Reuse a passed-in instance; only load if none provided
        if nlp is not None:
            self.nlp = nlp
        else:
            from config import SPACY_MODEL
            self.nlp = spacy.load(SPACY_MODEL)

    def extract(self, query: str) -> str:
        if not query or not query.strip():
            return ""

        query = query.strip().title()
        doc = self.nlp(query)

        # 1. Primary Strategy: Grab standard Geopolitical Entities (GPE) or General Locations (LOC)
        locations = [ent.text for ent in doc.ents if ent.label_ in LOCATION_ENTITY_LABELS]

        if locations:
            return " ".join(locations)

        # 2. Fallback Strategy: If spaCy NER misses a landmark (like Mount Rainier),
        # extract capitalized noun-phrases following spatial prepositions.
        preposition_pattern = r"\b(?:around|in|near|across|over|for|at|of)\s+([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)"
        match = re.search(preposition_pattern, query)
        if match:
            extracted_landmark = match.group(1)
            words = extracted_landmark.split()
            cleaned_words = [w for w in words if w not in LOCATION_NOISE_WORDS]
            if cleaned_words:
                return " ".join(cleaned_words)

        return ""
