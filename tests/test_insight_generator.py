from core.insight_generator import generate_insights


def test_high_video_streaming_generates_streaming_recommendation():
    """Video-heavy activity should be identified with a direct action."""

    result = generate_insights(
        {
            "screen_time_hours": 5.0,
            "video_streaming_hours": 4.0,
            "charging_sessions": 1,
            "social_media_hours": 1.0,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.0204, "energy_kwh": 0.0444},
    )

    assert result["summary"] == (
        "Your smartphone generated approximately 20 grams of CO2 today."
    )
    assert any("Video streaming" in driver for driver in result["top_drivers"])
    assert "Reduce video streaming by 30 minutes daily." in result[
        "recommended_actions"
    ]


def test_high_screen_time_generates_screen_time_recommendation():
    """High screen time should produce a screen-time action."""

    result = generate_insights(
        {
            "screen_time_hours": 8.0,
            "video_streaming_hours": 1.0,
            "charging_sessions": 1,
            "social_media_hours": 1.0,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.01},
    )

    assert any("screen time" in driver.lower() for driver in result["top_drivers"])
    assert "Reduce overall screen time by 30 minutes daily." in result[
        "recommended_actions"
    ]


def test_high_charging_sessions_generates_charging_recommendation():
    """Repeated charging should produce a charging-cycle action."""

    result = generate_insights(
        {
            "screen_time_hours": 3.0,
            "video_streaming_hours": 0.5,
            "charging_sessions": 4,
            "social_media_hours": 0.5,
            "music_streaming_hours": 0.5,
        },
        {"co2_kg": 0.015},
    )

    assert "Frequent charging increased energy consumption." in result[
        "top_drivers"
    ]
    assert "Avoid unnecessary charging cycles." in result[
        "recommended_actions"
    ]


def test_low_usage_profile_returns_maintenance_guidance():
    """Low daily activity should not be presented as a high-usage problem."""

    result = generate_insights(
        {
            "screen_time_hours": 1.0,
            "video_streaming_hours": 0.25,
            "charging_sessions": 0,
            "social_media_hours": 0.25,
            "music_streaming_hours": 0.25,
        },
        {"co2_kg": 0.001},
    )

    assert result["top_drivers"] == [
        "Your smartphone usage was low across the tracked activities."
    ]
    assert result["recommended_actions"] == [
        "Maintain your current low-usage habits."
    ]
