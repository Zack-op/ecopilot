from typing import Any, Dict, Mapping

from core.carbon_provider import CarbonProvider, MockCarbonProvider
from core.climatiq_provider import (
    DEFAULT_DATA_VERSION,
    DEFAULT_ELECTRICITY_ACTIVITY_ID,
    ClimatiqProvider,
    estimate_smartphone_energy_kwh,
)
from core.telemetry_parser import TelemetryPayload


def smartphone_payload() -> TelemetryPayload:
    """Build a representative smartphone telemetry payload."""

    return TelemetryPayload(
        user_id="user_01",
        device_type="android",
        stream_type="smartphone",
        metrics={
            "screen_time_hours": 6,
            "video_streaming_hours": 2,
            "charging_sessions": 1,
            "social_media_hours": 1.5,
            "music_streaming_hours": 0.5,
        },
    )


class StubClimatiqProvider(ClimatiqProvider):
    """Climatiq provider that avoids network calls in tests."""

    def __init__(self, response_body: Dict[str, Any]) -> None:
        super().__init__(api_key="test-key")
        self.response_body = response_body
        self.last_request_body: Mapping[str, Any] | None = None

    def _post_estimate(self, request_body: Mapping[str, Any]) -> Dict[str, Any]:
        self.last_request_body = request_body
        return self.response_body


class FakeFallbackProvider(CarbonProvider):
    """Fallback provider used to prove delegation when the API key is absent."""

    def __init__(self) -> None:
        self.called_with: TelemetryPayload | None = None

    def calculate(self, payload: TelemetryPayload) -> Dict[str, Any]:
        self.called_with = payload
        return {
            "co2_kg": 0.01,
            "category": "smartphone",
            "provider": "fake_fallback",
        }


def test_build_estimate_request_for_smartphone_payload():
    """Smartphone telemetry should map to a Climatiq estimate request."""

    provider = ClimatiqProvider(api_key="test-key")

    request_body = provider.build_estimate_request(smartphone_payload())

    assert request_body["emission_factor"] == {
        "activity_id": DEFAULT_ELECTRICITY_ACTIVITY_ID,
        "data_version": DEFAULT_DATA_VERSION,
        "region": "US",
    }
    assert request_body["parameters"] == {
        "energy": 0.0278,
        "energy_unit": "kWh",
    }


def test_calculate_posts_climatiq_request_and_returns_estimate():
    """A Climatiq response should be normalized to EcoPilot output fields."""

    provider = StubClimatiqProvider(
        {
            "co2e": 0.0123,
            "co2e_unit": "kg",
        }
    )

    result = provider.calculate(smartphone_payload())

    assert result == {
        "co2_kg": 0.0123,
        "co2_unit": "kg",
        "category": "smartphone",
        "provider": "climatiq",
        "energy_kwh": 0.0278,
    }
    assert provider.last_request_body is not None
    assert provider.last_request_body["parameters"]["energy_unit"] == "kWh"


def test_missing_api_key_uses_configured_fallback(monkeypatch):
    """Calculation should delegate when no Climatiq API key is available."""

    monkeypatch.delenv("CLIMATIQ_API_KEY", raising=False)
    fallback = FakeFallbackProvider()
    provider = ClimatiqProvider(api_key=None, fallback_provider=fallback)
    payload = smartphone_payload()

    result = provider.calculate(payload)

    assert fallback.called_with == payload
    assert result == {
        "co2_kg": 0.01,
        "category": "smartphone",
        "provider": "fake_fallback",
    }


def test_default_missing_api_key_fallback_is_mock_provider(monkeypatch):
    """The default fallback should be the existing MockCarbonProvider."""

    monkeypatch.delenv("CLIMATIQ_API_KEY", raising=False)

    provider = ClimatiqProvider(api_key=None)

    assert isinstance(provider.fallback_provider, MockCarbonProvider)


def test_unsupported_stream_type_with_api_key_returns_error():
    """ClimatiqProvider only handles smartphone telemetry itself."""

    provider = ClimatiqProvider(api_key="test-key")
    payload = TelemetryPayload(
        user_id="user_02",
        device_type="android",
        stream_type="mobility",
        metrics={
            "mode": "car",
            "distance_km": 10,
        },
    )

    result = provider.calculate(payload)

    assert "error" in result
    assert "Unsupported stream type: mobility" in result["error"]


def test_estimate_smartphone_energy_clamps_invalid_metrics():
    """Invalid or negative metric values should not reduce the estimate."""

    energy_kwh = estimate_smartphone_energy_kwh(
        {
            "screen_time_hours": -2,
            "video_streaming_hours": "bad",
            "charging_sessions": 1,
            "social_media_hours": None,
            "music_streaming_hours": 2,
        }
    )

    assert energy_kwh == 0.0132


def test_missing_co2e_in_climatiq_response_returns_error():
    """Malformed Climatiq responses should fail clearly."""

    provider = StubClimatiqProvider({"co2e_unit": "kg"})

    result = provider.calculate(smartphone_payload())

    assert "error" in result
    assert result["provider"] == "climatiq"
    assert "co2e" in result["error"]
