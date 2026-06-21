from typing import Any, Dict

from core.climatiq_provider import estimate_smartphone_energy_kwh
from persona_comparison import (
    PERSONAS,
    evaluate_persona,
    evaluate_personas,
    format_comparison_report,
)


class FakeCarbonProvider:
    """Deterministic carbon provider used to keep comparison tests offline."""

    def calculate(self, payload) -> Dict[str, Any]:
        energy_kwh = estimate_smartphone_energy_kwh(payload.metrics)
        return {
            "co2_kg": round(energy_kwh * 0.4, 4),
            "energy_kwh": energy_kwh,
            "category": "smartphone",
            "provider": "test",
        }


class FakeCoach:
    """Coach double that returns a stable explanation without an LLM call."""

    def generate(self, carbon_result, insight_result, goal_result) -> Dict[str, str]:
        return {"coach_message": "Practical coaching summary."}


def test_all_personas_execute_successfully():
    """Every supported simulator persona should complete the comparison flow."""

    results = evaluate_personas(
        carbon_provider=FakeCarbonProvider(),
        coach=FakeCoach(),
    )

    assert [result["persona"] for result in results] == list(PERSONAS)
    assert all(result["carbon_result"]["co2_kg"] >= 0 for result in results)
    assert all(result["coach_result"]["coach_message"] for result in results)


def test_comparison_report_includes_each_persona_and_summary():
    """The formatted report should present all persona intelligence outputs."""

    results = evaluate_personas(
        carbon_provider=FakeCarbonProvider(),
        coach=FakeCoach(),
    )

    report = format_comparison_report(results)

    assert "ECOPILOT PERSONA COMPARISON" in report
    assert "Carbon Footprint:" in report
    assert "Recommended Action:" in report
    assert "Coach Summary:" in report
    for persona in PERSONAS:
        assert f"Persona: {persona}" in report


def test_single_persona_evaluation_does_not_raise():
    """A direct persona evaluation should return every pipeline stage."""

    result = evaluate_persona(
        "Heavy User",
        carbon_provider=FakeCarbonProvider(),
        coach=FakeCoach(),
        rng_seed=200,
    )

    assert result["persona"] == "Heavy User"
    assert result["payload"].stream_type == "smartphone"
    assert result["insights"]["recommended_actions"]
    assert result["goal"]["status"] in {
        "below_target",
        "on_target",
        "above_target",
    }
