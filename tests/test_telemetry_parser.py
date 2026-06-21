from core.telemetry_parser import validate_payload

def test_valid_payload():
    data = {
        "user_id":"user_01",
        "device_type":"android",
        "stream_type":"mobility",
        "metrics":{
            "mode":"car",
            "distance_km":20
        }
    }

    result = validate_payload(data)

    assert result["status"] == "success"

def test_missing_user_id():
    data = {
        "device_type":"android",
        "stream_type":"mobility",
        "metrics":{}
    }

    result = validate_payload(data)

    assert result["status"] == "error"