from config import DEFAULT_BUFFER_KM


class QueryRouter:
    """
    Routes parsed NLP requests into exact instruction sets for the
    underlying Earth Observation data pipeline execution block.
    """

    def __init__(self):
        pass

    def route(self, request: dict) -> dict:
        mode = request["mode"]

        if mode == "snapshot":
            return self._route_snapshot(request)
        elif mode == "temporal":
            return self._route_temporal(request)

        raise ValueError(f"Unsupported mode pipeline flag: {mode}")

    def _route_snapshot(self, request: dict) -> dict:
        return {
            "pipeline": "snapshot",
            "location": request["location"],
            "index": request["index"],
            "buffer_km": request.get("buffer_km", DEFAULT_BUFFER_KM)
        }

    def _route_temporal(self, request: dict) -> dict:
        return {
            "pipeline": "temporal",
            "location": request["location"],
            "index": request["index"],
            "buffer_km": request.get("buffer_km", DEFAULT_BUFFER_KM),
            "pre_window": request.get("pre_window"),
            "post_window": request.get("post_window")
        }