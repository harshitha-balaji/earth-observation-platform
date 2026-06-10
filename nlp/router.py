from nlp.routes import SnapshotRoute, TemporalRoute

class QueryRouter:
    """
    Routes parsed NLP inputs into explicit, validated dataclass signatures
    for downstream platform calculations.
    """

    def __init__(self) -> None:
        pass

    def route(self, request: dict):
        mode = request["mode"]

        if mode == "snapshot":
            return SnapshotRoute(
                location=request["location"],
                index=request["index"],
                buffer_km=float(request.get("buffer_km") or 5.0)
            )
        elif mode == "temporal":
            return TemporalRoute(
                location=request["location"],
                index=request["index"],
                buffer_km=float(request.get("buffer_km") or 5.0),
                pre_window=request.get("pre_window"),
                post_window=request.get("post_window")
            )

        raise ValueError(f"Unsupported pipeline execution flag: {mode}")