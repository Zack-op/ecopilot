# core/telemetry_parser.py

from datetime import datetime, UTC
from typing import Dict, Any

from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    user_id: str
    device_type: str

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    stream_type: str

    metrics: Dict[str, Any]

def validate_payload(raw_data: dict):
    try:
        payload = TelemetryPayload(**raw_data)

        return {
            "status": "success",
            "payload": payload
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":

    sample_data = {
        "user_id": "user_01",
        "device_type": "android",
        "stream_type": "mobility",
        "metrics": {
            "mode": "car",
            "distance_km": 20
        }
    }

    result = validate_payload(sample_data)

    print(result)