import json
from pathlib import Path
from typing import Any


def load_posts(path: str | Path) -> list[dict[str, Any]]:
    """Load a list of raw post objects from a local JSON file."""
    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of posts in {input_path}")

    return payload
