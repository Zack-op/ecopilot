from core.goal_tracker import track_goal


def test_below_target_reports_target_met():
    """Lower daily emissions should be below the target."""

    result = track_goal(daily_co2_kg=0.01, target_co2_kg=0.015)

    assert result == {
        "status": "below_target",
        "difference_kg": 0.005,
        "progress_percent": 100.0,
        "message": "You are below your sustainability target.",
    }


def test_above_target_reports_progress_percentage():
    """Higher daily emissions should report remaining target progress."""

    result = track_goal(daily_co2_kg=0.0204, target_co2_kg=0.015)

    assert result == {
        "status": "above_target",
        "difference_kg": 0.0054,
        "progress_percent": 73.5,
        "message": "You are 73.5% toward your sustainability target.",
    }


def test_exact_target_reports_on_target():
    """Equal daily and target emissions should be on target."""

    result = track_goal(daily_co2_kg=0.015, target_co2_kg=0.015)

    assert result == {
        "status": "on_target",
        "difference_kg": 0.0,
        "progress_percent": 100.0,
        "message": "You are on your sustainability target.",
    }


def test_zero_target_handles_zero_and_positive_daily_emissions():
    """A zero-emission target must avoid division by zero."""

    assert track_goal(daily_co2_kg=0.0, target_co2_kg=0.0)["status"] == "on_target"

    result = track_goal(daily_co2_kg=0.01, target_co2_kg=0.0)

    assert result == {
        "status": "above_target",
        "difference_kg": 0.01,
        "progress_percent": 0.0,
        "message": "You are 0.0% toward your sustainability target.",
    }
