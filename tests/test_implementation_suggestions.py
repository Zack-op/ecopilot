"""Tests for implementation suggestion generation feature."""

import pytest
from core.llm_insight_generator import (
    LLMInsightGenerator,
    build_local_action_suggestions,
    build_suggestion_prompt,
    _parse_suggestions_from_response,
)


class TestImplementationSuggestions:
    """Test suite for implementation suggestion generation."""

    def test_suggestions_generated_for_contributors(self):
        """Implementation suggestions should be generated for each contributor."""
        
        insight_result = {
            "contributors": [
                {
                    "rank": 1,
                    "category": "Video Streaming",
                    "reason": "High usage",
                    "action": "Reduce video streaming by 30 minutes daily.",
                },
                {
                    "rank": 2,
                    "category": "Screen Time",
                    "reason": "High usage",
                    "action": "Reduce overall screen time by 30 minutes daily.",
                },
            ]
        }
        
        generator = LLMInsightGenerator()
        suggestions = generator.generate_implementation_suggestions(insight_result)
        
        # Should have suggestions for both contributors
        assert isinstance(suggestions, dict)
        assert 0 in suggestions  # Contributor at index 0
        assert 1 in suggestions  # Contributor at index 1
        assert len(suggestions[0]) > 0
        assert len(suggestions[1]) > 0


    def test_suggestions_empty_for_no_contributors(self):
        """No suggestions should be generated for empty contributor list."""
        
        insight_result = {
            "contributors": []
        }
        
        generator = LLMInsightGenerator()
        suggestions = generator.generate_implementation_suggestions(insight_result)
        
        assert suggestions == {}


    def test_local_video_streaming_suggestions(self):
        """Video streaming action should generate streaming-specific suggestions."""
        
        action = "Reduce video streaming by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert any("episode" in s.lower() or "watch" in s.lower() for s in suggestions)
        assert any("stream" in s.lower() or "viewing" in s.lower() for s in suggestions)


    def test_local_screen_time_suggestions(self):
        """Screen time action should generate screen-specific suggestions."""
        
        action = "Reduce overall screen time by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert any("grayscale" in s.lower() or "screen" in s.lower() for s in suggestions)


    def test_local_social_media_suggestions(self):
        """Social media action should generate social-specific suggestions."""
        
        action = "Set a daily social media time limit."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert any("notification" in s.lower() or "timer" in s.lower() for s in suggestions)


    def test_local_charging_suggestions(self):
        """Charging action should generate charging-specific suggestions."""
        
        action = "Avoid unnecessary charging cycles."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert any("charge" in s.lower() or "battery" in s.lower() for s in suggestions)


    def test_local_music_streaming_suggestions(self):
        """Music streaming action should generate music-specific suggestions."""
        
        action = "Download playlists over Wi-Fi for offline listening."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert any("download" in s.lower() or "offline" in s.lower() or "playlist" in s.lower() for s in suggestions)


    def test_generic_suggestions_fallback(self):
        """Unknown action should return generic suggestions."""
        
        action = "Some unknown action about reducing carbon."
        suggestions = build_local_action_suggestions(action)
        
        assert len(suggestions) == 3
        assert all(isinstance(s, str) for s in suggestions)


    def test_suggestions_are_concise(self):
        """All suggestions should be concise (one sentence each)."""
        
        action = "Reduce video streaming by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        for suggestion in suggestions:
            # Each suggestion should be a single sentence
            assert suggestion.endswith('.')
            # Suggestions should not be too long
            assert len(suggestion) < 100


    def test_suggestion_prompt_includes_action(self):
        """Suggestion prompt should include the supplied action."""
        
        action = "Reduce video streaming by 30 minutes daily."
        prompt = build_suggestion_prompt(action)
        
        assert action in prompt
        assert "Do NOT generate a new action" in prompt
        assert "Do NOT modify the supplied action" in prompt


    def test_suggestion_prompt_constrains_llm(self):
        """Suggestion prompt should prevent LLM from generating new actions."""
        
        action = "Some action"
        prompt = build_suggestion_prompt(action)
        
        # Verify all critical constraints are in prompt
        assert "Do NOT generate a new action" in prompt
        assert "Do NOT modify the supplied action" in prompt
        assert "Do NOT suggest alternatives to the supplied action" in prompt
        assert "Do NOT introduce new sustainability recommendations" in prompt
        assert "Generate ONLY implementation ideas" in prompt


    def test_parse_suggestions_from_response(self):
        """Should extract bullet-point suggestions from LLM response."""
        
        response = """Here are ways to achieve this:
- Watch one fewer episode per day.
- Set a fixed viewing window for streaming.
- Replace streaming time with offline activities."""
        
        suggestions = _parse_suggestions_from_response(response)
        
        assert len(suggestions) == 3
        assert "Watch one fewer episode per day." in suggestions
        assert "Set a fixed viewing window for streaming." in suggestions
        assert "Replace streaming time with offline activities." in suggestions


    def test_parse_suggestions_with_asterisks(self):
        """Should extract suggestions marked with asterisks."""
        
        response = """* First suggestion
* Second suggestion
* Third suggestion"""
        
        suggestions = _parse_suggestions_from_response(response)
        
        assert len(suggestions) == 3


    def test_parse_suggestions_limits_to_three(self):
        """Parser should return maximum 3 suggestions."""
        
        response = """- Suggestion 1
- Suggestion 2
- Suggestion 3
- Suggestion 4
- Suggestion 5"""
        
        suggestions = _parse_suggestions_from_response(response)
        
        assert len(suggestions) <= 3


    def test_suggestions_correspond_to_action(self):
        """Suggestions should directly support the supplied action."""
        
        action = "Reduce video streaming by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        # Verify suggestions relate to streaming/video
        suggestion_text = " ".join(suggestions).lower()
        assert any(word in suggestion_text for word in [
            "stream", "video", "watch", "episode", "viewing", "activity"
        ])


    def test_suggestions_not_contradicting_action(self):
        """Suggestions should not contradict the supplied action."""
        
        action = "Reduce video streaming by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        # Suggestions should not suggest increasing streaming
        for suggestion in suggestions:
            assert "increase" not in suggestion.lower()
            assert "more video" not in suggestion.lower()
            assert "more streaming" not in suggestion.lower()


    def test_multiple_contributors_all_get_suggestions(self):
        """All contributors with actions should get suggestions."""
        
        insight_result = {
            "contributors": [
                {
                    "rank": 1,
                    "category": "Video Streaming",
                    "reason": "High",
                    "action": "Reduce video streaming by 30 minutes daily.",
                },
                {
                    "rank": 2,
                    "category": "Screen Time",
                    "reason": "High",
                    "action": "Reduce overall screen time by 30 minutes daily.",
                },
                {
                    "rank": 3,
                    "category": "Social Media",
                    "reason": "Medium",
                    "action": "Set a daily social media time limit.",
                },
            ]
        }
        
        generator = LLMInsightGenerator()
        suggestions = generator.generate_implementation_suggestions(insight_result)
        
        # Should have suggestions for all 3
        assert len(suggestions) == 3
        for i in range(3):
            assert i in suggestions
            assert len(suggestions[i]) > 0


    def test_missing_action_handled_gracefully(self):
        """Contributors without action should be skipped."""
        
        insight_result = {
            "contributors": [
                {
                    "rank": 1,
                    "category": "Video Streaming",
                    "reason": "High",
                    # Missing action
                },
                {
                    "rank": 2,
                    "category": "Screen Time",
                    "reason": "High",
                    "action": "Reduce overall screen time by 30 minutes daily.",
                },
            ]
        }
        
        generator = LLMInsightGenerator()
        suggestions = generator.generate_implementation_suggestions(insight_result)
        
        # Only contributor with action should have suggestions
        assert len(suggestions) == 1
        assert 1 in suggestions


    def test_suggestions_practicality(self):
        """All suggestions should be practical and low-friction."""
        
        action = "Reduce video streaming by 30 minutes daily."
        suggestions = build_local_action_suggestions(action)
        
        # Verify suggestions are actionable
        for suggestion in suggestions:
            # Should contain action verbs or specific recommendations
            assert len(suggestion) > 5  # Not too short
            assert len(suggestion) < 100  # Not too long


    def test_suggestion_endpoint_backward_compatible(self):
        """New suggestion endpoint should not break existing coach functionality."""
        
        generator = LLMInsightGenerator()
        
        # Old coach generation should still work
        coach_result = generator.generate(
            {"co2_kg": 0.025},
            {"top_drivers": ["Test"], "recommended_actions": ["Action"]},
            {"status": "on_target", "progress_percent": 50.0},
        )
        
        assert "coach_message" in coach_result
        assert isinstance(coach_result["coach_message"], str)
