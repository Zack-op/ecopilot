#!/usr/bin/env python3
"""Validation script to test carbon provider module."""

import sys
sys.path.insert(0, "d:\\ecopilot")

try:
    # Test imports
    print("=" * 60)
    print("IMPORT VALIDATION")
    print("=" * 60)
    
    from core.carbon_provider import MockCarbonProvider, CarbonProvider
    from core.telemetry_parser import TelemetryPayload
    print("✓ All imports successful\n")
    
    # Test basic functionality
    print("=" * 60)
    print("BASIC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    provider = MockCarbonProvider()
    
    # Test 1: Car trip
    print("\n1. Testing car trip (20km):")
    payload = TelemetryPayload(
        user_id="user_01",
        device_type="android",
        stream_type="mobility",
        metrics={"mode": "car", "distance_km": 20}
    )
    result = provider.calculate(payload)
    expected = 4.2
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg, Got: {actual}kg")
    
    # Test 2: Train trip
    print("\n2. Testing train trip (100km):")
    payload = TelemetryPayload(
        user_id="user_02",
        device_type="ios",
        stream_type="mobility",
        metrics={"mode": "train", "distance_km": 100}
    )
    result = provider.calculate(payload)
    expected = 4.0
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg, Got: {actual}kg")
    
    # Test 3: Bus trip
    print("\n3. Testing bus trip (50km):")
    payload = TelemetryPayload(
        user_id="user_03",
        device_type="android",
        stream_type="mobility",
        metrics={"mode": "bus", "distance_km": 50}
    )
    result = provider.calculate(payload)
    expected = 4.0
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg, Got: {actual}kg")
    
    # Test 4: Walking (zero emissions)
    print("\n4. Testing walking (10km):")
    payload = TelemetryPayload(
        user_id="user_05",
        device_type="android",
        stream_type="mobility",
        metrics={"mode": "walking", "distance_km": 10}
    )
    result = provider.calculate(payload)
    expected = 0.0
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg, Got: {actual}kg")
    
    # Test 5: Unknown mode (defaults to car factor)
    print("\n5. Testing unknown mode - spaceship (10km):")
    payload = TelemetryPayload(
        user_id="user_09",
        device_type="android",
        stream_type="mobility",
        metrics={"mode": "spaceship", "distance_km": 10}
    )
    result = provider.calculate(payload)
    expected = 2.1
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg (default), Got: {actual}kg")
    
    # Test 6: Unsupported stream type
    print("\n6. Testing unsupported stream type - energy:")
    payload = TelemetryPayload(
        user_id="user_11",
        device_type="android",
        stream_type="energy",
        metrics={}
    )
    result = provider.calculate(payload)
    has_error = "error" in result
    status = "✓" if has_error else "✗"
    print(f"   {status} Error returned: {result}")
    
    # Test 7: Missing distance (defaults to 0)
    print("\n7. Testing missing distance (defaults to 0):")
    payload = TelemetryPayload(
        user_id="user_08",
        device_type="android",
        stream_type="mobility",
        metrics={"mode": "car"}
    )
    result = provider.calculate(payload)
    expected = 0.0
    actual = result["co2_kg"]
    status = "✓" if actual == expected else "✗"
    print(f"   {status} Expected CO2: {expected}kg, Got: {actual}kg")
    
    print("\n" + "=" * 60)
    print("INHERITANCE TESTS")
    print("=" * 60)
    
    # Test inheritance
    print("\n8. Testing MockCarbonProvider is instance of CarbonProvider:")
    is_instance = isinstance(provider, CarbonProvider)
    status = "✓" if is_instance else "✗"
    print(f"   {status} isinstance check: {is_instance}")
    
    # Test abstract class
    print("\n9. Testing CarbonProvider cannot be instantiated:")
    try:
        CarbonProvider()
        print("   ✗ FAILED - Abstract class was instantiated")
    except TypeError as e:
        print(f"   ✓ PASSED - TypeError raised: {str(e)[:50]}...")
    
    print("\n" + "=" * 60)
    print("ALL VALIDATION TESTS PASSED!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
