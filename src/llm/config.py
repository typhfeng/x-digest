from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_PROVIDER = "openai_compatible"
DEFAULT_TIMEOUT_SECONDS = 20.0
CONFIG_ENV_VAR = "X_DIGEST_CONFIG"


@dataclass(frozen=True, slots=True)
class LlmSettings:
    """Optional configuration for LLM-assisted summarization."""

    enabled: bool = False
    provider: str = DEFAULT_PROVIDER
    model: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    api_key: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(
            self.enabled
            and self.provider
            and self.model
            and self.base_url
            and self.api_key
        )


def load_llm_settings(
    *,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> LlmSettings:
    """Load LLM settings from environment variables and an optional JSON config file."""
    env_map = dict(os.environ if env is None else env)
    config = _load_config_file(env_map, cwd=cwd)
    llm_config = config.get("llm", {})

    enabled = _read_bool(env_map.get("X_DIGEST_LLM_ENABLED"), llm_config.get("enabled", False))
    provider = str(env_map.get("X_DIGEST_LLM_PROVIDER", llm_config.get("provider", DEFAULT_PROVIDER)))
    model = _read_optional_string(env_map.get("X_DIGEST_LLM_MODEL"), llm_config.get("model"))
    base_url = str(env_map.get("X_DIGEST_LLM_BASE_URL", llm_config.get("base_url", DEFAULT_BASE_URL)))
    timeout_seconds = _read_float(
        env_map.get("X_DIGEST_LLM_TIMEOUT"),
        llm_config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
    )
    api_key = _read_optional_string(
        env_map.get("X_DIGEST_LLM_API_KEY") or env_map.get("OPENAI_API_KEY"),
        None,
    )

    return LlmSettings(
        enabled=enabled,
        provider=provider.strip(),
        model=model,
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout_seconds,
        api_key=api_key,
    )


def _load_config_file(
    env: dict[str, str],
    *,
    cwd: str | Path | None,
) -> dict[str, Any]:
    raw_path = env.get(CONFIG_ENV_VAR)
    if not raw_path:
        return {}

    config_path = Path(cwd or ".") / raw_path if not Path(raw_path).is_absolute() else Path(raw_path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _read_bool(raw_value: str | None, default: Any) -> bool:
    if raw_value is None:
        if isinstance(default, bool):
            return default
        if default is None:
            return False
        return str(default).strip().casefold() in {"1", "true", "yes", "on"}

    normalized = raw_value.strip().casefold()
    return normalized in {"1", "true", "yes", "on"}


def _read_float(raw_value: str | None, default: Any) -> float:
    if raw_value is None:
        return float(default)

    try:
        return float(raw_value)
    except ValueError:
        return float(default)


def _read_optional_string(primary: str | None, fallback: Any) -> str | None:
    value = primary if primary is not None else fallback
    if value is None:
        return None

    stripped = str(value).strip()
    return stripped or None
