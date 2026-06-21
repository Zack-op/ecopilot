"""Climatiq-backed carbon provider for smartphone telemetry."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

from typing import Any, Dict, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.carbon_provider import CarbonProvider, MockCarbonProvider
from core.telemetry_parser import TelemetryPayload


CLIMATIQ_ESTIMATE_URL = "https://api.climatiq.io/data/v1/estimate"
DEFAULT_ELECTRICITY_ACTIVITY_ID = "electricity-supply_grid-source_residual_mix"
DEFAULT_DATA_VERSION = "^34"

SMARTPHONE_ENERGY_FACTORS_KWH = {
    "screen_time_hours": 0.0012,
    "video_streaming_hours": 0.0030,
    "charging_sessions": 0.0120,
    "social_media_hours": 0.0015,
    "music_streaming_hours": 0.0006,
}


class ClimatiqProvider(CarbonProvider):
    """Carbon provider that estimates smartphone telemetry with Climatiq.

    The provider maps EcoPilot smartphone telemetry into Climatiq's basic
    estimate request shape. If no API key is available, calculation is
    delegated to MockCarbonProvider so local tests can still run offline.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        fallback_provider: CarbonProvider | None = None,
        api_url: str = CLIMATIQ_ESTIMATE_URL,
        activity_id: str = DEFAULT_ELECTRICITY_ACTIVITY_ID,
        data_version: str = DEFAULT_DATA_VERSION,
        region: str = "US",
        timeout_seconds: float = 10.0,
    ) -> None:
        """Initialize the provider.

        Args:
            api_key: Climatiq API key. Defaults to CLIMATIQ_API_KEY.
            fallback_provider: Provider used when no API key is available.
            api_url: Climatiq estimate endpoint URL.
            activity_id: Climatiq electricity emission factor activity ID.
            data_version: Climatiq data version selector.
            region: Emission factor region selector.
            timeout_seconds: HTTP request timeout.
        """

        self.api_key = api_key or os.getenv("CLIMATIQ_API_KEY")
        self.fallback_provider = fallback_provider or MockCarbonProvider()
        self.api_url = api_url
        self.activity_id = activity_id
        self.data_version = data_version
        self.region = region
        self.timeout_seconds = timeout_seconds

    def calculate(self, payload: TelemetryPayload) -> Dict[str, Any]:
        """Return a carbon estimate for a smartphone telemetry payload."""

        if not self.api_key:
            return self.fallback_provider.calculate(payload)
        if payload.stream_type != "smartphone":
            return {
                "error": f"Unsupported stream type: {payload.stream_type}"
            }

        request_body = self.build_estimate_request(payload)
        response_body = self._post_estimate(request_body)

        if "error" in response_body:
            return response_body

        co2e = response_body.get("co2e")
        if co2e is None:
            return {
                "error": "Climatiq response did not include co2e",
                "provider": "climatiq",
                "raw_response": response_body,
            }

        return {
            "co2_kg": co2e,
            "co2_unit": response_body.get("co2e_unit", "kg"),
            "category": "smartphone",
            "provider": "climatiq",
            "energy_kwh": request_body["parameters"]["energy"],
        }

    def build_estimate_request(self, payload: TelemetryPayload) -> Dict[str, Any]:
        """Build a Climatiq-compatible estimate request body."""

        if payload.stream_type != "smartphone":
            raise ValueError(f"Unsupported stream type: {payload.stream_type}")

        energy_kwh = estimate_smartphone_energy_kwh(payload.metrics)

        return {
            "emission_factor": {
                "activity_id": self.activity_id,
                "data_version": self.data_version,
                "region": self.region,
            },
            "parameters": {
                "energy": energy_kwh,
                "energy_unit": "kWh",
            },
        }

    def _post_estimate(self, request_body: Mapping[str, Any]) -> Dict[str, Any]:
        """Post an estimate request to Climatiq and return decoded JSON."""

        request = Request(
            self.api_url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return {
                "error": f"Climatiq API request failed with status {exc.code}",
                "provider": "climatiq",
                "details": _read_error_body(exc),
            }
        except URLError as exc:
            return {
                "error": f"Climatiq API request failed: {exc.reason}",
                "provider": "climatiq",
            }
        except json.JSONDecodeError as exc:
            return {
                "error": f"Climatiq API response was not valid JSON: {exc}",
                "provider": "climatiq",
            }


def estimate_smartphone_energy_kwh(metrics: Mapping[str, Any]) -> float:
    """Estimate daily smartphone electricity use from telemetry metrics."""

    energy_kwh = 0.0

    for metric_name, factor in SMARTPHONE_ENERGY_FACTORS_KWH.items():
        metric_value = _metric_as_non_negative_float(metrics.get(metric_name, 0.0))
        energy_kwh += metric_value * factor

    return round(energy_kwh, 4)


def _metric_as_non_negative_float(value: Any) -> float:
    """Convert metric values to floats while preventing negative usage."""

    try:
        return max(float(value), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _read_error_body(exc: HTTPError) -> str:
    """Read an HTTP error response body when Climatiq provides one."""

    try:
        return exc.read().decode("utf-8")
    except Exception:
        return ""
