"""Smartphone telemetry simulator for EcoPilot test data.

The simulator creates daily usage payloads shaped for the existing
TelemetryPayload schema in core.telemetry_parser.
"""

from __future__ import annotations

from random import Random
from typing import Any, Dict, Literal, Mapping, Tuple


PersonaName = Literal["student", "office_worker", "heavy_user", "minimal_user"]

MetricRange = Tuple[float, float]


PERSONA_ALIASES: Mapping[str, PersonaName] = {
    "student": "student",
    "office worker": "office_worker",
    "office_worker": "office_worker",
    "heavy user": "heavy_user",
    "heavy_user": "heavy_user",
    "minimal user": "minimal_user",
    "minimal_user": "minimal_user",
}


PERSONA_USAGE_RANGES: Mapping[PersonaName, Mapping[str, MetricRange]] = {
    "student": {
        "screen_time_hours": (4.0, 8.0),
        "video_streaming_hours": (1.0, 3.0),
        "charging_sessions": (1.0, 2.0),
        "social_media_hours": (1.0, 3.0),
        "music_streaming_hours": (0.5, 2.5),
    },
    "office_worker": {
        "screen_time_hours": (3.0, 6.0),
        "video_streaming_hours": (0.25, 1.5),
        "charging_sessions": (1.0, 2.0),
        "social_media_hours": (0.5, 1.5),
        "music_streaming_hours": (0.25, 1.5),
    },
    "heavy_user": {
        "screen_time_hours": (8.0, 12.0),
        "video_streaming_hours": (3.0, 6.0),
        "charging_sessions": (2.0, 4.0),
        "social_media_hours": (2.5, 5.0),
        "music_streaming_hours": (1.0, 4.0),
    },
    "minimal_user": {
        "screen_time_hours": (0.5, 2.5),
        "video_streaming_hours": (0.0, 0.75),
        "charging_sessions": (0.0, 1.0),
        "social_media_hours": (0.0, 0.75),
        "music_streaming_hours": (0.0, 1.0),
    },
}


def generate_daily_usage(
    persona: str,
    *,
    rng: Random | None = None,
) -> Dict[str, float | int]:
    """Generate realistic daily smartphone metrics for a persona.

    Args:
        persona: The user persona to simulate.
        rng: Optional random generator, useful for deterministic tests.

    Returns:
        A metrics dictionary compatible with TelemetryPayload.metrics.

    Raises:
        ValueError: If the persona is not supported.
    """

    normalized_persona = _normalize_persona(persona)

    randomizer = rng or Random()
    ranges = PERSONA_USAGE_RANGES[normalized_persona]

    return {
        "screen_time_hours": _random_hours(
            ranges["screen_time_hours"],
            randomizer,
        ),
        "video_streaming_hours": _random_hours(
            ranges["video_streaming_hours"],
            randomizer,
        ),
        "charging_sessions": _random_sessions(
            ranges["charging_sessions"],
            randomizer,
        ),
        "social_media_hours": _random_hours(
            ranges["social_media_hours"],
            randomizer,
        ),
        "music_streaming_hours": _random_hours(
            ranges["music_streaming_hours"],
            randomizer,
        ),
    }


def generate_smartphone_payload(
    user_id: str,
    persona: str,
    *,
    device_type: str = "android",
    rng: Random | None = None,
) -> Dict[str, Any]:
    """Generate a daily smartphone telemetry payload.

    Args:
        user_id: User identifier for the simulated telemetry event.
        persona: The user persona to simulate.
        device_type: Smartphone platform, such as ``android`` or ``ios``.
        rng: Optional random generator, useful for deterministic tests.

    Returns:
        A dictionary compatible with the TelemetryPayload schema.
    """

    return {
        "user_id": user_id,
        "device_type": device_type,
        "stream_type": "smartphone",
        "metrics": generate_daily_usage(persona, rng=rng),
    }


def _normalize_persona(persona: str) -> PersonaName:
    """Normalize supported persona labels to internal keys."""

    persona_key = persona.strip().lower().replace("-", " ")

    if persona_key in PERSONA_ALIASES:
        return PERSONA_ALIASES[persona_key]

    supported = ", ".join(
        ("Student", "Office Worker", "Heavy User", "Minimal User")
    )
    raise ValueError(f"Unsupported persona: {persona}. Supported personas: {supported}")


def _random_hours(value_range: MetricRange, rng: Random) -> float:
    """Return a rounded hour value from a range."""

    minimum, maximum = value_range
    return round(rng.uniform(minimum, maximum), 2)


def _random_sessions(value_range: MetricRange, rng: Random) -> int:
    """Return a whole-number charging session count from a range."""

    minimum, maximum = value_range
    return rng.randint(int(minimum), int(maximum))
