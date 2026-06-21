"""Run the complete EcoPilot V1 smartphone sustainability workflow."""

from __future__ import annotations

from random import Random
from typing import Any, Dict, Mapping

from core.climatiq_provider import ClimatiqProvider
from core.goal_tracker import track_goal
from core.insight_generator import generate_insights
from core.llm_insight_generator import LLMInsightGenerator
from core.smartphone_simulator import generate_smartphone_payload
from core.telemetry_parser import TelemetryPayload, validate_payload


DAILY_TARGET_CO2_KG = 0.0150
DEMO_USER_ID = "student"
DEMO_PERSONA = "Student"
DEMO_RANDOM_SEED = 42
REPORT_DIVIDER = "=" * 33


def run_pipeline() -> Dict[str, Any]:
    """Run the EcoPilot V1 workflow and return report-ready data.

    The seeded random generator makes this demonstration repeatable. A live
    Climatiq key is required because the completed mock provider does not
    calculate smartphone emissions.

    Returns:
        The persona, validated telemetry, carbon result, insights, goal,
        coach message, and implementation suggestions.

    Raises:
        RuntimeError: If telemetry validation or carbon calculation fails.
    """

    raw_payload = generate_smartphone_payload(
        user_id=DEMO_USER_ID,
        persona=DEMO_PERSONA,
        rng=Random(DEMO_RANDOM_SEED),
    )
    validation_result = validate_payload(raw_payload)

    if validation_result["status"] != "success":
        raise RuntimeError(
            f"Telemetry validation failed: {validation_result['message']}"
        )

    payload = validation_result["payload"]
    if not isinstance(payload, TelemetryPayload):
        raise RuntimeError("Telemetry validation did not return a payload.")

    provider = ClimatiqProvider()
    if not provider.api_key:
        raise RuntimeError(
            "CLIMATIQ_API_KEY is required to run the live EcoPilot demo."
        )

    carbon_result = provider.calculate(payload)
    if "error" in carbon_result:
        raise RuntimeError(f"Carbon calculation failed: {carbon_result['error']}")

    insights = generate_insights(payload.metrics, carbon_result)
    goal = track_goal(
        daily_co2_kg=carbon_result["co2_kg"],
        target_co2_kg=DAILY_TARGET_CO2_KG,
    )
    coach_generator = LLMInsightGenerator()
    coach_result = coach_generator.generate(
        carbon_result,
        insights,
        goal,
    )
    
    # Generate implementation suggestions for each contributor action
    suggestions_result = coach_generator.generate_implementation_suggestions(insights)

    return {
        "persona": DEMO_PERSONA.lower(),
        "payload": payload,
        "carbon_result": carbon_result,
        "insights": insights,
        "goal": goal,
        "coach_result": coach_result,
        "suggestions": suggestions_result,
    }


def format_report(pipeline_result: Mapping[str, Any]) -> str:
    """Format the pipeline output as a user-facing daily report."""

    carbon_result = pipeline_result["carbon_result"]
    insights = pipeline_result["insights"]
    goal = pipeline_result["goal"]
    coach_result = pipeline_result["coach_result"]
    suggestions = pipeline_result.get("suggestions", {})
    carbon_grams = float(carbon_result["co2_kg"]) * 1000
    energy_kwh = float(carbon_result["energy_kwh"])

    lines = [
        REPORT_DIVIDER,
        "ECOPILOT DAILY REPORT",
        REPORT_DIVIDER,
        "",
        "User:",
        str(pipeline_result["persona"]),
        "",
        "Carbon Footprint:",
        f"{carbon_grams:.1f} g CO2",
        "",
        "Energy Usage:",
        f"{energy_kwh:.4f} kWh",
        "",
    ]
    
    # Display contributors if available
    contributors = insights.get("contributors", [])
    if contributors:
        lines.extend((
            "Major Contributors:",
        ))
        for contrib in contributors:
            contrib_idx = contrib.get("rank", 1) - 1
            lines.extend((
                f"{contrib['rank']}. {contrib['category']}",
                f"   Action: {contrib['action']}",
            ))
            
            # Display implementation suggestions
            if contrib_idx in suggestions:
                lines.append("   Ways to achieve this:")
                for suggestion in suggestions[contrib_idx]:
                    lines.append(f"   • {suggestion}")
        lines.append("")
    else:
        # Fallback to old format
        lines.extend((
            "Top Drivers:",
            *[f"- {driver}" for driver in insights["top_drivers"]],
            "",
            "Recommendations:",
            *[f"- {action}" for action in insights["recommended_actions"]],
            "",
        ))
    
    lines.extend((
        "Goal Progress:",
        f"{goal['progress_percent']:.1f}%",
        "",
        "Status:",
        str(goal["status"]).replace("_", " ").title(),
        "",
        "AI Sustainability Coach:",
        str(coach_result["coach_message"]),
        "",
        REPORT_DIVIDER,
    ))
    return "\n".join(lines)


def main() -> None:
    """Execute the pipeline and print its daily sustainability report."""

    try:
        print(format_report(run_pipeline()))
    except RuntimeError as exc:
        raise SystemExit(f"EcoPilot demo could not complete: {exc}") from exc


if __name__ == "__main__":
    main()
