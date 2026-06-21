#!/usr/bin/env python3
"""Validate the implementation suggestions feature."""

import sys
sys.path.insert(0, 'd:\\ecopilot')

print("=" * 80)
print("ECOPILOT V1 ENHANCEMENT - IMPLEMENTATION SUGGESTIONS VALIDATION")
print("=" * 80)

try:
    # Test imports
    print("\n[1] Testing imports...")
    from core.llm_insight_generator import (
        LLMInsightGenerator,
        build_local_action_suggestions,
        build_suggestion_prompt,
        _parse_suggestions_from_response,
    )
    from core.insight_generator import generate_insights
    print("    ✓ All imports successful")

    # Test suggestion generation
    print("\n[2] Testing suggestion generation...")
    generator = LLMInsightGenerator()
    
    insights = generate_insights(
        {
            "screen_time_hours": 8.0,
            "video_streaming_hours": 3.5,
            "charging_sessions": 2,
            "social_media_hours": 2.0,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.025},
    )
    
    suggestions = generator.generate_implementation_suggestions(insights)
    print(f"    ✓ Suggestions generated")
    print(f"      - Number of contributors: {len(insights.get('contributors', []))}")
    print(f"      - Suggestions generated for: {len(suggestions)} contributors")

    # Verify suggestions correspond to actions
    print("\n[3] Verifying suggestions correspond to actions...")
    contributors = insights.get("contributors", [])
    for contrib_idx, contributor in enumerate(contributors):
        action = contributor.get("action", "")
        if contrib_idx in suggestions:
            suggestion_list = suggestions[contrib_idx]
            print(f"\n    Contributor {contrib_idx + 1}: {contributor['category']}")
            print(f"    Action: {action}")
            print(f"    Suggestions ({len(suggestion_list)}):")
            for i, sugg in enumerate(suggestion_list, 1):
                print(f"      {i}. {sugg}")
            
            # Verify suggestions support the action
            action_lower = action.lower()
            suggestion_text = " ".join(suggestion_list).lower()
            
            # Check for topic alignment
            if "video" in action_lower:
                assert any(word in suggestion_text for word in ["stream", "watch", "episode", "viewing"])
            if "screen" in action_lower:
                assert any(word in suggestion_text for word in ["screen", "app", "grayscale"])
            if "social" in action_lower:
                assert any(word in suggestion_text for word in ["notification", "timer", "limit", "app"])
            if "charg" in action_lower:
                assert any(word in suggestion_text for word in ["charge", "battery", "drain"])
            
            print(f"    ✓ Suggestions support the action")

    # Test local suggestions for each action type
    print("\n[4] Testing action-specific suggestions...")
    
    actions = {
        "video": "Reduce video streaming by 30 minutes daily.",
        "screen": "Reduce overall screen time by 30 minutes daily.",
        "social": "Set a daily social media time limit.",
        "charge": "Avoid unnecessary charging cycles.",
        "music": "Download playlists over Wi-Fi for offline listening.",
    }
    
    for action_type, action in actions.items():
        suggestions = build_local_action_suggestions(action)
        assert len(suggestions) == 3, f"Expected 3 suggestions for {action_type}, got {len(suggestions)}"
        print(f"    ✓ {action_type}: {len(suggestions)} suggestions")

    # Test suggestion prompt constraints
    print("\n[5] Testing suggestion prompt constraints...")
    prompt = build_suggestion_prompt("Test action")
    
    required_constraints = [
        "Do NOT generate a new action",
        "Do NOT modify the supplied action",
        "Do NOT suggest alternatives",
        "Do NOT introduce new sustainability recommendations",
        "Generate ONLY implementation ideas",
    ]
    
    for constraint in required_constraints:
        assert constraint in prompt, f"Missing constraint: {constraint}"
    
    print(f"    ✓ All constraints present in prompt")
    print(f"      - {len(required_constraints)} constraints verified")

    # Test response parsing
    print("\n[6] Testing response parsing...")
    response = """- Watch one fewer episode per day.
- Set a fixed viewing window.
- Replace streaming with another activity."""
    
    parsed = _parse_suggestions_from_response(response)
    assert len(parsed) == 3
    assert "Watch one fewer episode per day." in parsed
    print(f"    ✓ Response parsing works correctly")
    print(f"      - Extracted {len(parsed)} suggestions")

    # Test no action generation in suggestions
    print("\n[7] Verifying action generation NOT in suggestion layer...")
    
    # Insight Generator creates actions
    insight_action = insights["contributors"][0]["action"]
    assert len(insight_action) > 0
    print(f"    ✓ Actions created by Insight Generator: {insight_action[:50]}...")
    
    # LLM suggestions don't create new actions
    suggestions_for_action = generator.generate_implementation_suggestions(insights)
    # Suggestions are just implementation ideas
    for idx, sugg_list in suggestions_for_action.items():
        for sugg in sugg_list:
            # Suggestions should not be action statements
            # (they're support steps, not new actions)
            assert not sugg.endswith(" daily")  # Not a new daily action
    
    print(f"    ✓ Suggestion layer does NOT generate actions")

    # Test multiple contributor scenario
    print("\n[8] Testing multiple contributors...")
    insights_heavy = generate_insights(
        {
            "screen_time_hours": 9.0,
            "video_streaming_hours": 4.0,
            "charging_sessions": 3,
            "social_media_hours": 3.0,
            "music_streaming_hours": 2.5,
        },
        {"co2_kg": 0.035},
    )
    
    suggestions_heavy = generator.generate_implementation_suggestions(insights_heavy)
    contributors_heavy = insights_heavy.get("contributors", [])
    
    print(f"    - Heavy user contributors: {len(contributors_heavy)}")
    print(f"    - Suggestions generated for: {len(suggestions_heavy)}")
    assert len(suggestions_heavy) == len(contributors_heavy)
    print(f"    ✓ All contributors have suggestions")

    # Test backward compatibility
    print("\n[9] Testing backward compatibility...")
    
    # Old coach generation should still work
    coach_result = generator.generate(
        {"co2_kg": 0.025},
        insights,
        {"status": "on_target", "progress_percent": 50.0},
    )
    
    assert "coach_message" in coach_result
    assert len(coach_result["coach_message"]) > 0
    print(f"    ✓ Coach message generation still works")
    print(f"      - Message length: {len(coach_result['coach_message'])} chars")

    print("\n" + "=" * 80)
    print("✓ ALL VALIDATION TESTS PASSED!")
    print("=" * 80)
    print("\nImplementation Suggestions Feature Summary:")
    print("  ✓ Suggestions generated for each contributor action")
    print("  ✓ Suggestions correspond to supplied actions")
    print("  ✓ LLM constrained to suggestions only (not action generation)")
    print("  ✓ Deterministic fallback when LLM unavailable")
    print("  ✓ Action-specific suggestions for each category")
    print("  ✓ Response parsing from LLM output")
    print("  ✓ Multiple contributors fully supported")
    print("  ✓ Backward compatibility maintained")
    print("\nReady for full pytest suite! ✅")

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
