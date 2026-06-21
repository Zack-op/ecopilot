from core.smartphone_simulator import generate_smartphone_payload
from core.telemetry_parser import validate_payload
from core.climatiq_provider import ClimatiqProvider


payload = generate_smartphone_payload(
    user_id="user_01",
    persona="student"
)

print("RAW PAYLOAD:")
print(payload)

validated = validate_payload(payload)

print("\nVALIDATED:")
print(validated)

provider = ClimatiqProvider()

result = provider.calculate(
    validated["payload"]
)

print("\nCARBON RESULT:")
print(result)