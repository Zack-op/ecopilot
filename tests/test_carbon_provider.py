import pytest
from core.carbon_provider import MockCarbonProvider, CarbonProvider
from core.telemetry_parser import TelemetryPayload


class TestMockCarbonProvider:
    """Test suite for MockCarbonProvider carbon calculation."""

    def setup_method(self):
        """Initialize provider for each test."""
        self.provider = MockCarbonProvider()

    # ===== Mobility Transport Modes =====

    def test_car_trip(self):
        """Test CO2 calculation for car transport."""
        payload = TelemetryPayload(
            user_id="user_01",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "car",
                "distance_km": 20
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 4.2  # 20 * 0.21
        assert result["category"] == "transport"

    def test_train_trip(self):
        """Test CO2 calculation for train transport."""
        payload = TelemetryPayload(
            user_id="user_02",
            device_type="ios",
            stream_type="mobility",
            metrics={
                "mode": "train",
                "distance_km": 100
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 4.0  # 100 * 0.04
        assert result["category"] == "transport"

    def test_bus_trip(self):
        """Test CO2 calculation for bus transport."""
        payload = TelemetryPayload(
            user_id="user_03",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "bus",
                "distance_km": 50
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 4.0  # 50 * 0.08
        assert result["category"] == "transport"

    def test_metro_trip(self):
        """Test CO2 calculation for metro transport."""
        payload = TelemetryPayload(
            user_id="user_04",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "metro",
                "distance_km": 25
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 1.0  # 25 * 0.04
        assert result["category"] == "transport"

    def test_walking(self):
        """Test CO2 calculation for walking (zero emissions)."""
        payload = TelemetryPayload(
            user_id="user_05",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "walking",
                "distance_km": 10
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 0.0  # 10 * 0.0
        assert result["category"] == "transport"

    def test_bike(self):
        """Test CO2 calculation for biking (zero emissions)."""
        payload = TelemetryPayload(
            user_id="user_06",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "bike",
                "distance_km": 15
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 0.0  # 15 * 0.0
        assert result["category"] == "transport"

    # ===== Edge Cases =====

    def test_zero_distance(self):
        """Test CO2 calculation with zero distance."""
        payload = TelemetryPayload(
            user_id="user_07",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "car",
                "distance_km": 0
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 0.0
        assert result["category"] == "transport"

    def test_missing_distance(self):
        """Test CO2 calculation with missing distance (defaults to 0)."""
        payload = TelemetryPayload(
            user_id="user_08",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "car"
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 0.0  # 0 * 0.21
        assert result["category"] == "transport"

    def test_unknown_transport_mode(self):
        """Test CO2 calculation with unknown transport mode (defaults to car factor)."""
        payload = TelemetryPayload(
            user_id="user_09",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "spaceship",
                "distance_km": 10
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 2.1  # 10 * 0.21 (default)
        assert result["category"] == "transport"

    def test_large_distance(self):
        """Test CO2 calculation with large distance."""
        payload = TelemetryPayload(
            user_id="user_10",
            device_type="android",
            stream_type="mobility",
            metrics={
                "mode": "car",
                "distance_km": 1000
            }
        )
        result = self.provider.calculate(payload)
        assert result["co2_kg"] == 210.0  # 1000 * 0.21
        assert result["category"] == "transport"

    # ===== Error Handling =====

    def test_unsupported_stream_type(self):
        """Test error handling for unsupported stream types."""
        payload = TelemetryPayload(
            user_id="user_11",
            device_type="android",
            stream_type="energy",
            metrics={}
        )
        result = self.provider.calculate(payload)
        assert "error" in result
        assert "Unsupported stream type: energy" in result["error"]

    def test_unsupported_stream_type_food(self):
        """Test error handling for food stream type."""
        payload = TelemetryPayload(
            user_id="user_12",
            device_type="android",
            stream_type="food",
            metrics={}
        )
        result = self.provider.calculate(payload)
        assert "error" in result
        assert "Unsupported stream type: food" in result["error"]

    # ===== Inheritance & Abstract Method =====

    def test_carbon_provider_is_abstract(self):
        """Test that CarbonProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            CarbonProvider()

    def test_mock_provider_is_carbon_provider(self):
        """Test that MockCarbonProvider is a CarbonProvider instance."""
        assert isinstance(self.provider, CarbonProvider)