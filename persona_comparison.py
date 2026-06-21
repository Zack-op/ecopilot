"""Compare EcoPilot's intelligence output across smartphone user personas."""

from __future__ import annotations

from random import Random
from typing import Any, Dict, Mapping, Sequence

from core.carbon_provider import CarbonProvider
from core.climatiq_provider import ClimatiqProvider
from core.goal_tracker import track_goal
from core.insight_generator import generate_insights
from core.llm_insight_generator import LLMInsightGenerator
from core.smartphone_simulator import generate_smartphone_payload
from core.telemetry_parser import TelemetryPayload, validate_payload


PERSONAS = ("Student", "Office Worker", "Heavy User", "Minimal User")
DAILY_TARGET_CO2_KG = 0.0150
REPORT_DIVIDER = "=" * 51


def evaluate_persona(
    persona: str,
    *,
    carbon_provider: CarbonProvider,
    coach: LLMInsightGenerator,
    rng_seed: int,
) -> Dict[str, Any]:
    """Run one simulated persona through the existing EcoPilot workflow.

    Args:
        persona: Supported smartphone simulator persona.
        carbon_provider: Existing provider used for carbon calculations.
        coach: Existing LLM coach used only for natural-language explanation.
        rng_seed: Stable seed for repeatable comparison output.

    Returns:
        The persona's telemetry, carbon, insight, goal, coach, and suggestions results.

    Raises:
        RuntimeError: If telemetry validation or carbon calculation fails.
    """

    raw_payload = generate_smartphone_payload(
        user_id=persona.lower().replace(" ", "_"),
        persona=persona,
        rng=Random(rng_seed),
    )
    validation_result = validate_payload(raw_payload)

    if validation_result["status"] != "success":
        raise RuntimeError(
            f"Telemetry validation failed for {persona}: "
            f"{validation_result['message']}"
        )

    payload = validation_result["payload"]
    if not isinstance(payload, TelemetryPayload):
        raise RuntimeError(f"Telemetry validation did not return a payload for {persona}.")

    carbon_result = carbon_provider.calculate(payload)
    if "error" in carbon_result:
        raise RuntimeError(
            f"Carbon calculation failed for {persona}: {carbon_result['error']}"
        )

    insights = generate_insights(payload.metrics, carbon_result)
    goal = track_goal(
        daily_co2_kg=carbon_result["co2_kg"],
        target_co2_kg=DAILY_TARGET_CO2_KG,
    )
    coach_result = coach.generate(carbon_result, insights, goal)
    
    # Generate implementation suggestions for each contributor action
    suggestions_result = coach.generate_implementation_suggestions(insights)

    return {
        "persona": persona,
        "payload": payload,
        "carbon_result": carbon_result,
        "insights": insights,
        "goal": goal,
        "coach_result": coach_result,
        "suggestions": suggestions_result,
    }


def evaluate_personas(
    *,
    carbon_provider: CarbonProvider | None = None,
    coach: LLMInsightGenerator | None = None,
) -> list[Dict[str, Any]]:
    """Evaluate all supported personas with shared existing EcoPilot modules."""

    provider = carbon_provider or ClimatiqProvider()
    if isinstance(provider, ClimatiqProvider) and not provider.api_key:
        raise RuntimeError(
            "CLIMATIQ_API_KEY is required to run the live persona comparison."
        )

    coach_generator = coach or LLMInsightGenerator()
    return [
        evaluate_persona(
            persona,
            carbon_provider=provider,
            coach=coach_generator,
            rng_seed=100 + index,
        )
        for index, persona in enumerate(PERSONAS)
    ]


def format_comparison_report(persona_results: Sequence[Mapping[str, Any]]) -> str:
    """Format evaluated persona results as a clean console comparison report."""

    lines = [REPORT_DIVIDER, "ECOPILOT PERSONA COMPARISON", REPORT_DIVIDER]

    for result in persona_results:
        carbon_result = result["carbon_result"]
        insights = result["insights"]
        goal = result["goal"]
        coach_result = result["coach_result"]
        suggestions = result.get("suggestions", {})
        carbon_grams = float(carbon_result["co2_kg"]) * 1000

        lines.extend(
            (
                "",
                f"Persona: {result['persona']}",
                "",
                "Carbon Footprint:",
                f"{carbon_grams:.1f} g CO2",
                "",
            )
        )

        # Display contributors if available
        contributors = insights.get("contributors", [])
        if contributors:
            lines.extend(
                (
                    "Major Contributors Identified:",
                )
            )
            for contrib in contributors:
                contrib_idx = contrib.get("rank", 1) - 1
                lines.extend(
                    (
                        f"{contrib['rank']}. {contrib['category']}",
                        f"   {contrib['action']}",
                    )
                )
                
                # Display implementation suggestions for this contributor
                if contrib_idx in suggestions:
                    lines.append("   Ways to achieve this:")
                    for suggestion in suggestions[contrib_idx]:
                        lines.append(f"   • {suggestion}")
        else:
            # Fall back to top driver and action
            lines.extend(
                (
                    "Top Driver:",
                    _first_text(insights.get("top_drivers")),
                    "",
                    "Recommended Action:",
                    _first_text(insights.get("recommended_actions")),
                )
            )

        lines.extend(
            (
                "",
                "Goal Progress:",
                f"{float(goal['progress_percent']):.1f}%",
                "",
                "Coach Summary:",
                str(coach_result.get("coach_message", "Unavailable")).replace(
                    "\n", " "
                ),
                "",
                "---",
            )
        )

    lines.append(REPORT_DIVIDER)
    return "\n".join(lines)


def _first_text(value: Any) -> str:
    """Return the first existing insight item for report presentation."""

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            text = str(item).strip()
            if text:
                return text
    return "Unavailable"


def main() -> None:
    """Run the live comparison and print its console report."""

    try:
        print(format_comparison_report(evaluate_personas()))
    except RuntimeError as exc:
        raise SystemExit(f"EcoPilot comparison could not complete: {exc}") from exc


if __name__ == "__main__":
    main()
