from random import Random

import pytest

from core.smartphone_simulator import (
    PERSONA_USAGE_RANGES,
    generate_daily_usage,
    generate_smartphone_payload,
)
from core.telemetry_parser import TelemetryPayload, validate_payload


REQUIRED_METRICS = {
    "screen_time_hours",
    "video_streaming_hours",
    "charging_sessions",
    "social_media_hours",
    "music_streaming_hours",
}


def test_generated_payload_matches_telemetry_schema():
    """Generated simulator output should validate as a TelemetryPayload."""

    payload = generate_smartphone_payload(
        "user_01",
        "student",
        device_type="ios",
        rng=Random(42),
    )

    result = validate_payload(payload)

    assert result["status"] == "success"
    assert isinstance(result["payload"], TelemetryPayload)
    assert result["payload"].user_id == "user_01"
    assert result["payload"].device_type == "ios"
    assert result["payload"].stream_type == "smartphone"
    assert set(result["payload"].metrics) == REQUIRED_METRICS


@pytest.mark.parametrize("persona", PERSONA_USAGE_RANGES)
def test_all_personas_generate_metrics_in_expected_ranges(persona):
    """Each supported persona should generate realistic daily metrics."""

    metrics = generate_daily_usage(persona, rng=Random(7))

    assert set(metrics) == REQUIRED_METRICS

    for metric_name, value_range in PERSONA_USAGE_RANGES[persona].items():
        minimum, maximum = value_range
        assert minimum <= metrics[metric_name] <= maximum

    assert isinstance(metrics["charging_sessions"], int)
    assert isinstance(metrics["screen_time_hours"], float)
    assert isinstance(metrics["video_streaming_hours"], float)
    assert isinstance(metrics["social_media_hours"], float)
    assert isinstance(metrics["music_streaming_hours"], float)


def test_seeded_generation_is_deterministic():
    """An injected random generator should make simulator output repeatable."""

    first_payload = generate_smartphone_payload(
        "user_02",
        "office_worker",
        rng=Random(99),
    )
    second_payload = generate_smartphone_payload(
        "user_02",
        "office_worker",
        rng=Random(99),
    )

    assert first_payload == second_payload


def test_human_readable_persona_names_are_supported():
    """Personas from the product spec should work as input labels."""

    payload = generate_smartphone_payload(
        "user_03",
        "Office Worker",
        rng=Random(11),
    )

    assert payload["stream_type"] == "smartphone"
    assert set(payload["metrics"]) == REQUIRED_METRICS


def test_invalid_persona_raises_value_error():
    """Unsupported personas should fail clearly."""

    with pytest.raises(ValueError, match="Unsupported persona"):
        generate_daily_usage("commuter", rng=Random(1))  # type: ignore[arg-type]
