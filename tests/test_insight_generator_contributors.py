"""Tests for the new multi-contributor insight generation feature."""

from core.insight_generator import generate_insights


def test_single_contributor_user():
    """Low-usage user should have zero or one contributor."""

    result = generate_insights(
        {
            "screen_time_hours": 3.5,
            "video_streaming_hours": 1.0,
            "charging_sessions": 1,
            "social_media_hours": 0.5,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.005},
    )

    # Should have contributors list (may be empty)
    assert "contributors" in result
    assert isinstance(result["contributors"], list)
    # Should have 0 or 1 contributors for this low-usage profile
    assert len(result["contributors"]) <= 1


def test_multiple_contributor_user():
    """Heavy-usage user should have multiple contributors."""

    result = generate_insights(
        {
            "screen_time_hours": 8.0,
            "video_streaming_hours": 3.5,
            "charging_sessions": 3,
            "social_media_hours": 2.5,
            "music_streaming_hours": 1.5,
        },
        {"co2_kg": 0.025},
    )

    # Should have contributors list
    assert "contributors" in result
    assert isinstance(result["contributors"], list)
    # Should have multiple contributors for this heavy-usage profile
    assert len(result["contributors"]) >= 2


def test_contributor_ranking_by_impact():
    """Contributors should be ranked by usage impact (highest ratio first)."""

    result = generate_insights(
        {
            "screen_time_hours": 8.0,  # 8/6 = 1.33 ratio
            "video_streaming_hours": 4.0,  # 4/2 = 2.0 ratio (highest)
            "charging_sessions": 1,  # 1/2 = 0.5 ratio (below 0.6 minimum)
            "social_media_hours": 0.5,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.02},
    )

    contributors = result["contributors"]
    assert len(contributors) >= 2

    # Video streaming (2.0 ratio) should rank before screen time (1.33 ratio)
    assert contributors[0]["category"] == "Video Streaming"
    assert contributors[0]["rank"] == 1
    assert contributors[1]["category"] == "Screen Time"
    assert contributors[1]["rank"] == 2


def test_contributor_structure():
    """Each contributor should have rank, category, reason, and action."""

    result = generate_insights(
        {
            "screen_time_hours": 7.0,
            "video_streaming_hours": 2.5,
            "charging_sessions": 1,
            "social_media_hours": 1.0,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.015},
    )

    contributors = result["contributors"]
    assert len(contributors) > 0

    for contrib in contributors:
        assert "rank" in contrib
        assert isinstance(contrib["rank"], int)
        assert contrib["rank"] > 0

        assert "category" in contrib
        assert isinstance(contrib["category"], str)
        assert len(contrib["category"]) > 0

        assert "reason" in contrib
        assert isinstance(contrib["reason"], str)
        assert len(contrib["reason"]) > 0

        assert "action" in contrib
        assert isinstance(contrib["action"], str)
        assert len(contrib["action"]) > 0


def test_contributor_categories_correct():
    """Contributor categories should match expected values."""

    result = generate_insights(
        {
            "screen_time_hours": 7.0,
            "video_streaming_hours": 2.5,
            "charging_sessions": 3.0,
            "social_media_hours": 2.5,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.02},
    )

    contributors = result["contributors"]
    categories = {c["category"] for c in contributors}

    # All contributors should have proper category names
    valid_categories = {
        "Screen Time",
        "Video Streaming",
        "Charging",
        "Social Media",
        "Music Streaming",
    }
    for cat in categories:
        assert cat in valid_categories


def test_low_usage_below_threshold():
    """Metrics below minimum ratio (0.6 * threshold) should not appear."""

    # Video streaming at 1.0 hours is below 60% of 2.0 threshold
    result = generate_insights(
        {
            "screen_time_hours": 1.0,  # 1/6 = 0.167 (below 0.6)
            "video_streaming_hours": 1.0,  # 1/2 = 0.5 (below 0.6)
            "charging_sessions": 0.5,  # 0.5/2 = 0.25 (below 0.6)
            "social_media_hours": 0.5,  # 0.5/2 = 0.25 (below 0.6)
            "music_streaming_hours": 0.5,  # 0.5/2 = 0.25 (below 0.6)
        },
        {"co2_kg": 0.001},
    )

    # Should have no contributors
    assert result["contributors"] == []


def test_charging_metric_high_usage():
    """Charging should be properly ranked even though it's a count not hours."""

    result = generate_insights(
        {
            "screen_time_hours": 2.0,  # 2/6 = 0.33 (below 0.6)
            "video_streaming_hours": 0.5,  # 0.5/2 = 0.25 (below 0.6)
            "charging_sessions": 4.0,  # 4/2 = 2.0 ratio (high)
            "social_media_hours": 0.5,  # 0.5/2 = 0.25 (below 0.6)
            "music_streaming_hours": 0.5,  # 0.5/2 = 0.25 (below 0.6)
        },
        {"co2_kg": 0.015},
    )

    contributors = result["contributors"]
    assert len(contributors) >= 1
    assert contributors[0]["category"] == "Charging"
    assert "Avoid unnecessary charging cycles" in contributors[0]["action"]


def test_backward_compatibility_top_drivers():
    """Old code expecting top_drivers should still work."""

    result = generate_insights(
        {
            "screen_time_hours": 7.0,
            "video_streaming_hours": 2.5,
            "charging_sessions": 1,
            "social_media_hours": 1.0,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.015},
    )

    # Old fields should still exist
    assert "top_drivers" in result
    assert "recommended_actions" in result
    assert isinstance(result["top_drivers"], list)
    assert isinstance(result["recommended_actions"], list)
    assert len(result["top_drivers"]) > 0
    assert len(result["recommended_actions"]) > 0


def test_all_high_usage_metrics():
    """All metrics above threshold should appear as contributors."""

    result = generate_insights(
        {
            "screen_time_hours": 8.0,  # Above 6.0
            "video_streaming_hours": 3.0,  # Above 2.0
            "charging_sessions": 3.0,  # Above 2.0
            "social_media_hours": 3.0,  # Above 2.0
            "music_streaming_hours": 2.5,  # Above 2.0
        },
        {"co2_kg": 0.03},
    )

    contributors = result["contributors"]
    # All 5 metrics above threshold
    assert len(contributors) == 5

    # Check they're properly ranked
    for i, contrib in enumerate(contributors):
        assert contrib["rank"] == i + 1


def test_contributor_actions_are_distinct():
    """Each contributor should have an appropriate action for their category."""

    result = generate_insights(
        {
            "screen_time_hours": 7.0,
            "video_streaming_hours": 2.5,
            "charging_sessions": 3.0,
            "social_media_hours": 2.5,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.02},
    )

    contributors = result["contributors"]
    actions_by_category = {c["category"]: c["action"] for c in contributors}

    # Screen Time action should mention screen time
    if "Screen Time" in actions_by_category:
        assert "screen time" in actions_by_category["Screen Time"].lower()

    # Video Streaming action should mention video streaming
    if "Video Streaming" in actions_by_category:
        assert "video streaming" in actions_by_category["Video Streaming"].lower()

    # Charging action should mention charging
    if "Charging" in actions_by_category:
        assert "charging" in actions_by_category["Charging"].lower()

    # Social Media action should mention social media
    if "Social Media" in actions_by_category:
        assert "social media" in actions_by_category["Social Media"].lower()

    # Music Streaming action should mention music or playlist
    if "Music Streaming" in actions_by_category:
        action = actions_by_category["Music Streaming"].lower()
        assert "music" in action or "playlist" in action
