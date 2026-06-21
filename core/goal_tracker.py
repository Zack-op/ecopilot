"""Stateless sustainability goal calculations."""

from __future__ import annotations

import math
from typing import Any, Dict


def track_goal(daily_co2_kg: float, target_co2_kg: float) -> Dict[str, Any]:
    """Compare a daily carbon result against a sustainability target.

    A lower daily emission is better. Progress therefore expresses how close
    the target is to the current daily value and is capped at 100 percent once
    the target has been met.

    Args:
        daily_co2_kg: Carbon emitted during the day, in kilograms.
        target_co2_kg: Desired maximum daily carbon emission, in kilograms.

    Returns:
        The target status, absolute difference in kilograms, progress percent,
        and a user-friendly status message.

    Raises:
        ValueError: If either value is negative, non-numeric, or non-finite.
    """

    daily = _validate_emission_value(daily_co2_kg, "daily_co2_kg")
    target = _validate_emission_value(target_co2_kg, "target_co2_kg")
    difference = round(abs(daily - target), 4)

    if math.isclose(daily, target, abs_tol=1e-12):
        return {
            "status": "on_target",
            "difference_kg": 0.0,
            "progress_percent": 100.0,
            "message": "You are on your sustainability target.",
        }

    if daily < target:
        return {
            "status": "below_target",
            "difference_kg": difference,
            "progress_percent": 100.0,
            "message": "You are below your sustainability target.",
        }

    progress_percent = 0.0 if target == 0 else round((target / daily) * 100, 1)
    return {
        "status": "above_target",
        "difference_kg": difference,
        "progress_percent": progress_percent,
        "message": (
            f"You are {progress_percent:.1f}% toward your sustainability "
            "target."
        ),
    }


def _validate_emission_value(value: Any, field_name: str) -> float:
    """Validate an emission value before using it in a goal calculation."""

    try:
        converted = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a non-negative number") from exc

    if not math.isfinite(converted) or converted < 0:
        raise ValueError(f"{field_name} must be a non-negative number")

    return converted
