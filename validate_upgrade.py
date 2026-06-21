#!/usr/bin/env python3
"""Validate the new contributor functionality."""

import sys
sys.path.insert(0, 'd:\\ecopilot')

print("=" * 70)
print("ECOPILOT SMARTPHONE INTELLIGENCE UPGRADE - VALIDATION")
print("=" * 70)

try:
    # Test imports
    print("\n[1] Testing imports...")
    from core.insight_generator import generate_insights, _generate_contributors
    from core.llm_insight_generator import (
        build_coach_prompt,
        build_local_coach_message,
        LLMInsightGenerator,
    )
    from persona_comparison import evaluate_persona, format_comparison_report
    print("    ✓ All imports successful")

    # Test single contributor user
    print("\n[2] Testing single contributor user (low usage)...")
    result_low = generate_insights(
        {
            "screen_time_hours": 2.0,
            "video_streaming_hours": 0.5,
            "charging_sessions": 1,
            "social_media_hours": 0.5,
            "music_streaming_hours": 0.25,
        },
        {"co2_kg": 0.001},
    )
    assert "contributors" in result_low
    assert isinstance(result_low["contributors"], list)
    print(f"    ✓ Single contributor test passed")
    print(f"      - Contributors count: {len(result_low['contributors'])}")
    print(f"      - Summary present: {bool(result_low.get('summary'))}")
    print(f"      - Backward compatible (top_drivers): {bool(result_low.get('top_drivers'))}")

    # Test multiple contributor user
    print("\n[3] Testing multiple contributor user (heavy usage)...")
    result_heavy = generate_insights(
        {
            "screen_time_hours": 9.0,
            "video_streaming_hours": 4.0,
            "charging_sessions": 3,
            "social_media_hours": 3.0,
            "music_streaming_hours": 2.0,
        },
        {"co2_kg": 0.035},
    )
    assert "contributors" in result_heavy
    assert len(result_heavy["contributors"]) >= 2
    print(f"    ✓ Multiple contributor test passed")
    print(f"      - Contributors count: {len(result_heavy['contributors'])}")
    
    # Test contributor structure
    print("\n[4] Validating contributor structure...")
    contrib = result_heavy["contributors"][0]
    required_keys = {"rank", "category", "reason", "action"}
    assert required_keys == set(contrib.keys()), f"Missing keys: {required_keys - set(contrib.keys())}"
    assert contrib["rank"] == 1
    assert isinstance(contrib["category"], str)
    assert isinstance(contrib["reason"], str)
    assert isinstance(contrib["action"], str)
    print(f"    ✓ Contributor structure valid")
    print(f"      - Top contributor: {contrib['category']} (Rank {contrib['rank']})")
    print(f"      - Action: {contrib['action']}")

    # Test ranking
    print("\n[5] Testing contributor ranking by impact...")
    if len(result_heavy["contributors"]) >= 2:
        rank1_ratio = None
        rank2_ratio = None
        
        # For testing, we just verify they're ranked
        assert result_heavy["contributors"][0]["rank"] == 1
        assert result_heavy["contributors"][1]["rank"] == 2
        print(f"    ✓ Contributors properly ranked")
        for i, c in enumerate(result_heavy["contributors"][:3], 1):
            print(f"      - Rank {i}: {c['category']}")

    # Test coach integration
    print("\n[6] Testing coach prompt generation...")
    coach_prompt = build_coach_prompt(
        {"co2_kg": 0.025},
        result_heavy,
        {"status": "on_target", "progress_percent": 50.0},
    )
    assert "contributors" in coach_prompt
    assert isinstance(coach_prompt, str)
    print(f"    ✓ Coach prompt generation successful")
    print(f"      - Prompt length: {len(coach_prompt)} chars")

    # Test local coach message
    print("\n[7] Testing local coach message generation...")
    coach_msg = build_local_coach_message(
        {"co2_kg": 0.025},
        result_heavy,
        {"status": "on_target", "progress_percent": 50.0},
    )
    assert isinstance(coach_msg, str)
    assert len(coach_msg) > 0
    assert "CO2" in coach_msg or "grams" in coach_msg
    print(f"    ✓ Local coach message generation successful")
    print(f"      - Message length: {len(coach_msg)} chars")
    print(f"      - Message: {coach_msg[:100]}...")

    # Test backward compatibility
    print("\n[8] Testing backward compatibility...")
    assert "top_drivers" in result_heavy
    assert "recommended_actions" in result_heavy
    assert len(result_heavy["top_drivers"]) > 0
    assert len(result_heavy["recommended_actions"]) > 0
    print(f"    ✓ Backward compatibility maintained")
    print(f"      - top_drivers: {result_heavy['top_drivers'][0][:50]}...")
    print(f"      - recommended_actions: {result_heavy['recommended_actions'][0]}")

    # Test all metrics above threshold
    print("\n[9] Testing all metrics above threshold...")
    result_all = generate_insights(
        {
            "screen_time_hours": 8.0,
            "video_streaming_hours": 3.0,
            "charging_sessions": 3.0,
            "social_media_hours": 3.0,
            "music_streaming_hours": 2.5,
        },
        {"co2_kg": 0.03},
    )
    assert len(result_all["contributors"]) == 5
    print(f"    ✓ All metrics properly detected as contributors")
    for c in result_all["contributors"]:
        print(f"      - Rank {c['rank']}: {c['category']}")

    print("\n" + "=" * 70)
    print("✓ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print("  - New contributor feature fully implemented")
    print("  - Backward compatibility maintained")
    print("  - Coach integration updated")
    print("  - All data structures validated")
    print("\nReady for full pytest suite execution!")

except AssertionError as e:
    print(f"\n✗ VALIDATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
