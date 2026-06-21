from abc import ABC, abstractmethod

class CarbonProvider(ABC):

    @abstractmethod
    def calculate(self, payload):
        pass

class MockCarbonProvider(CarbonProvider):

    def calculate(self, payload):

        stream_type = payload.stream_type

        if stream_type == "mobility":

            mode = payload.metrics.get("mode")
            distance = payload.metrics.get("distance_km", 0)

            factors = {
                "car": 0.21,
                "train": 0.04,
                "bus": 0.08,
                "walking": 0.0,
                "bike": 0.0,
                "metro": 0.04,
            }

            return {
                "co2_kg": distance * factors.get(mode, 0.21), 
                "category": "transport"
            }
        else:
            return {
                "error": f"Unsupported stream type: {stream_type}"
            }