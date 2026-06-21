"""Rule-based sustainability insights for smartphone telemetry."""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping


USAGE_METRICS = (
    "screen_time_hours",
    "video_streaming_hours",
    "charging_sessions",
    "social_media_hours",
    "music_streaming_hours",
)

METRIC_LABELS = {
    "screen_time_hours": "Screen time",
    "video_streaming_hours": "Video streaming",
    "charging_sessions": "Charging sessions",
    "social_media_hours": "Social media usage",
    "music_streaming_hours": "Music streaming",
}

METRIC_CATEGORIES = {
    "screen_time_hours": "Screen Time",
    "video_streaming_hours": "Video Streaming",
    "charging_sessions": "Charging",
    "social_media_hours": "Social Media",
    "music_streaming_hours": "Music Streaming",
}

RECOMMENDATIONS = {
    "screen_time_hours": "Reduce overall screen time by 30 minutes daily.",
    "video_streaming_hours": "Reduce video streaming by 30 minutes daily.",
    "charging_sessions": "Avoid unnecessary charging cycles.",
    "social_media_hours": "Set a daily social media time limit.",
    "music_streaming_hours": "Download playlists over Wi-Fi for offline listening.",
}

CONTRIBUTOR_REASONS = {
    "screen_time_hours": "High screen time increased your phone's energy use.",
    "video_streaming_hours": "Video streaming was a major contributor to your energy use.",
    "charging_sessions": "Frequent charging increased energy consumption.",
    "social_media_hours": "Social media usage was a notable part of your screen time.",
    "music_streaming_hours": "Music streaming contributed to your smartphone energy use.",
}

HIGH_USAGE_THRESHOLDS = {
    "screen_time_hours": 6.0,
    "video_streaming_hours": 2.0,
    "charging_sessions": 2.0,
    "social_media_hours": 2.0,
    "music_streaming_hours": 2.0,
}

# Minimum usage ratio to include as a contributor (threshold multiple)
MIN_CONTRIBUTOR_RATIO = 0.6


def generate_insights(
    metrics: Mapping[str, Any],
    carbon_result: Mapping[str, Any],
) -> Dict[str, Any]:
    """Create deterministic sustainability insights from daily smartphone data.

    The generator compares each metric to a fixed daily high-usage threshold.
    This keeps different units, such as hours and charging sessions, comparable
    while avoiding any external model or service dependency.

    Args:
        metrics: Smartphone usage values from a telemetry payload.
        carbon_result: Carbon calculation output containing ``co2_kg``.

    Returns:
        A summary, identified usage drivers, actionable recommendations,
        and detailed contributors ranked by impact.
    """

    usage = {
        metric_name: _as_non_negative_float(metrics.get(metric_name, 0.0))
        for metric_name in USAGE_METRICS
    }
    co2_kg = _as_non_negative_float(carbon_result.get("co2_kg", 0.0))
    co2_grams = round(co2_kg * 1000)

    # Generate detailed contributors ranked by impact
    contributors = _generate_contributors(usage)
    
    # Extract top drivers and actions for backward compatibility
    highest_metric = max(USAGE_METRICS, key=lambda name: usage[name])
    driver_metrics = _select_driver_metrics(usage, highest_metric)

    if not driver_metrics:
        return {
            "summary": (
                f"Your smartphone generated approximately {co2_grams} grams "
                "of CO2 today."
            ),
            "top_drivers": [
                "Your smartphone usage was low across the tracked activities."
            ],
            "recommended_actions": [
                "Maintain your current low-usage habits."
            ],
            "contributors": [],
        }

    return {
        "summary": (
            f"Your smartphone generated approximately {co2_grams} grams "
            "of CO2 today."
        ),
        "top_drivers": [
            _driver_message(metric_name)
            for metric_name in driver_metrics
        ],
        "recommended_actions": [
            RECOMMENDATIONS[metric_name]
            for metric_name in driver_metrics
        ],
        "contributors": contributors,
    }


def _select_driver_metrics(
    usage: Mapping[str, float],
    highest_metric: str,
) -> list[str]:
    """Return up to two high-usage metrics ordered by threshold impact."""

    high_metrics = [
        metric_name
        for metric_name in USAGE_METRICS
        if usage[metric_name] >= HIGH_USAGE_THRESHOLDS[metric_name]
    ]

    if not high_metrics:
        return []

    high_metrics.sort(
        key=lambda name: (
            usage[name] / HIGH_USAGE_THRESHOLDS[name],
            name == highest_metric,
        ),
        reverse=True,
    )
    return high_metrics[:2]


def _generate_contributors(usage: Mapping[str, float]) -> list[Dict[str, Any]]:
    """Generate detailed contributors ranked by usage impact.
    
    Returns a list of contributors where each has rank, category, reason, and action.
    Contributors are ordered by their usage ratio (actual / threshold).
    """
    
    contributors = []
    
    # Calculate impact ratios for all metrics
    impact_metrics = []
    for metric_name in USAGE_METRICS:
        threshold = HIGH_USAGE_THRESHOLDS[metric_name]
        actual_usage = usage[metric_name]
        ratio = actual_usage / threshold if threshold > 0 else 0.0
        
        # Include metrics at or above minimum contributor ratio of threshold
        if ratio >= MIN_CONTRIBUTOR_RATIO:
            impact_metrics.append({
                "metric": metric_name,
                "usage": actual_usage,
                "threshold": threshold,
                "ratio": ratio,
            })
    
    # Sort by impact ratio (descending)
    impact_metrics.sort(key=lambda x: x["ratio"], reverse=True)
    
    # Create contributor objects
    for rank, item in enumerate(impact_metrics, start=1):
        metric_name = item["metric"]
        contributors.append({
            "rank": rank,
            "category": METRIC_CATEGORIES[metric_name],
            "reason": CONTRIBUTOR_REASONS[metric_name],
            "action": RECOMMENDATIONS[metric_name],
        })
    
    return contributors


def _driver_message(metric_name: str) -> str:
    """Describe a notable smartphone activity in user-facing language."""

    if metric_name == "video_streaming_hours":
        return "Video streaming was a major contributor to your energy use."
    if metric_name == "charging_sessions":
        return "Frequent charging increased energy consumption."
    if metric_name == "screen_time_hours":
        return "High screen time increased your phone's energy use."
    if metric_name == "social_media_hours":
        return "Social media usage was a notable part of your screen time."
    return "Music streaming contributed to your smartphone energy use."


def _as_non_negative_float(value: Any) -> float:
    """Convert a usage or carbon value to a finite non-negative float."""

    try:
        converted = float(value)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(converted):
        return 0.0

    return max(converted, 0.0)
