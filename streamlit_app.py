"""
EcoPilot - Personal Carbon Intelligence

A Streamlit UI for the EcoPilot smartphone sustainability analysis platform.
Displays carbon footprint, energy usage, goal progress, and personalized
sustainability recommendations with LLM-generated implementation suggestions.

This app reuses the existing EcoPilot backend pipeline without modifications.
"""

from __future__ import annotations

import streamlit as st
from random import Random
from typing import Any, Dict, Mapping

from core.climatiq_provider import ClimatiqProvider
from core.goal_tracker import track_goal
from core.insight_generator import generate_insights
from core.llm_insight_generator import LLMInsightGenerator
from core.smartphone_simulator import generate_smartphone_payload
from core.telemetry_parser import TelemetryPayload, validate_payload


# Configuration
DAILY_TARGET_CO2_KG = 0.0150
PERSONAS = ["Student", "Office Worker", "Heavy User", "Minimal User"]
PERSONA_USER_IDS = {
    "Student": "student",
    "Office Worker": "office_worker",
    "Heavy User": "heavy_user",
    "Minimal User": "minimal_user",
}


def execute_ecopilot_pipeline(persona: str) -> Dict[str, Any] | None:
    """Execute the EcoPilot pipeline for a given persona.
    
    Args:
        persona: The user persona (Student, Office Worker, Heavy User, Minimal User)
        
    Returns:
        Dictionary with pipeline results (persona, carbon_result, insights, goal,
        coach_result, suggestions) or None if execution fails.
    """
    try:
        # Generate smartphone telemetry for the persona
        user_id = PERSONA_USER_IDS[persona]
        raw_payload = generate_smartphone_payload(
            user_id=user_id,
            persona=persona,
            rng=Random(),  # Non-deterministic for live demo
        )
        
        # Validate telemetry
        validation_result = validate_payload(raw_payload)
        if validation_result["status"] != "success":
            st.error(f"Telemetry validation failed: {validation_result['message']}")
            return None
        
        payload = validation_result["payload"]
        if not isinstance(payload, TelemetryPayload):
            st.error("Telemetry validation did not return a valid payload.")
            return None
        
        # Calculate carbon emissions
        provider = ClimatiqProvider()
        if not provider.api_key:
            st.error("⚠️ CLIMATIQ_API_KEY not configured. Using fallback calculations.")
            # Fallback: create a synthetic result for demo purposes
            carbon_result = {
                "co2_kg": 0.025,
                "energy_kwh": 0.12,
            }
        else:
            carbon_result = provider.calculate(payload)
            if "error" in carbon_result:
                st.error(f"Carbon calculation failed: {carbon_result['error']}")
                return None
        
        # Generate insights (contributors + recommendations)
        insights = generate_insights(payload.metrics, carbon_result)
        
        # Track goal progress
        goal = track_goal(
            daily_co2_kg=carbon_result["co2_kg"],
            target_co2_kg=DAILY_TARGET_CO2_KG,
        )
        
        # Generate coach message
        coach_generator = LLMInsightGenerator()
        coach_result = coach_generator.generate(
            carbon_result,
            insights,
            goal,
        )
        
        # Generate implementation suggestions
        suggestions_result = coach_generator.generate_implementation_suggestions(insights)
        
        return {
            "persona": persona.lower(),
            "payload": payload,
            "carbon_result": carbon_result,
            "insights": insights,
            "goal": goal,
            "coach_result": coach_result,
            "suggestions": suggestions_result,
        }
        
    except Exception as e:
        st.error(f"Pipeline execution error: {str(e)}")
        return None


def format_carbon_display(co2_kg: float) -> tuple[float, str]:
    """Convert CO2 from kg to grams and format for display.
    
    Args:
        co2_kg: CO2 in kilograms
        
    Returns:
        Tuple of (grams_value, formatted_string)
    """
    grams = co2_kg * 1000
    return grams, f"{grams:.1f}"


def display_metrics_section(pipeline_result: Dict[str, Any]) -> None:
    """Display key metrics in Streamlit columns.
    
    Args:
        pipeline_result: Result from execute_ecopilot_pipeline
    """
    carbon_result = pipeline_result["carbon_result"]
    goal = pipeline_result["goal"]
    
    co2_grams, co2_display = format_carbon_display(carbon_result["co2_kg"])
    energy_kwh = float(carbon_result["energy_kwh"])
    progress_percent = goal["progress_percent"]
    status = str(goal["status"]).replace("_", " ").title()
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💨 Carbon Footprint",
            value=co2_display,
            delta="g CO2",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            label="⚡ Energy Usage",
            value=f"{energy_kwh:.4f}",
            delta="kWh",
        )
    
    with col3:
        st.metric(
            label="🎯 Goal Progress",
            value=f"{progress_percent:.1f}%",
            delta="of daily target",
        )
    
    with col4:
        st.metric(
            label="📊 Status",
            value=status,
            delta="",
        )


def display_goal_progress_bar(pipeline_result: Dict[str, Any]) -> None:
    """Display goal progress as a visual progress bar.
    
    Args:
        pipeline_result: Result from execute_ecopilot_pipeline
    """
    goal = pipeline_result["goal"]
    progress_percent = min(goal["progress_percent"] / 100.0, 1.0)  # Cap at 100%
    
    st.progress(progress_percent, text=f"Goal Progress: {goal['progress_percent']:.1f}%")


def display_contributors_section(pipeline_result: Dict[str, Any]) -> None:
    """Display major contributors with actions and suggestions using expanders.
    
    Args:
        pipeline_result: Result from execute_ecopilot_pipeline
    """
    insights = pipeline_result["insights"]
    suggestions = pipeline_result.get("suggestions", {})
    contributors = insights.get("contributors", [])
    
    if not contributors:
        st.info("No major contributors identified. Your usage is balanced! 🌱")
        return
    
    st.subheader("🔍 Major Contributors")
    
    for contributor in contributors:
        rank = contributor.get("rank", 1)
        category = contributor.get("category", "Unknown")
        reason = contributor.get("reason", "")
        action = contributor.get("action", "")
        contrib_idx = rank - 1
        
        with st.expander(f"**{rank}. {category}**", expanded=(rank == 1)):
            st.write(f"**Reason:** {reason}")
            st.write(f"**Action:** {action}")
            
            # Display implementation suggestions if available
            if contrib_idx in suggestions and suggestions[contrib_idx]:
                st.write("**Ways to achieve this:**")
                for suggestion in suggestions[contrib_idx]:
                    st.write(f"• {suggestion}")
            else:
                st.write("*No suggestions available for this contributor.*")


def display_coach_section(pipeline_result: Dict[str, Any]) -> None:
    """Display AI Sustainability Coach message in a dedicated section.
    
    Args:
        pipeline_result: Result from execute_ecopilot_pipeline
    """
    coach_result = pipeline_result["coach_result"]
    coach_message = coach_result.get("coach_message", "")
    
    st.subheader("🤖 AI Sustainability Coach")
    
    with st.container(border=True):
        st.write(coach_message)


def display_metrics_detail_section(pipeline_result: Dict[str, Any]) -> None:
    """Display detailed smartphone metrics breakdown.
    
    Args:
        pipeline_result: Result from execute_ecopilot_pipeline
    """
    payload = pipeline_result["payload"]
    
    st.subheader("📱 Smartphone Usage Metrics")
    
    # Display metrics in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Screen Time**")
        st.write(f"{payload.metrics.get('screen_time_hours', 0):.1f} hours")
        
        st.write("**Video Streaming**")
        st.write(f"{payload.metrics.get('video_streaming_hours', 0):.1f} hours")
        
        st.write("**Music Streaming**")
        st.write(f"{payload.metrics.get('music_streaming_hours', 0):.1f} hours")
    
    with col2:
        st.write("**Social Media**")
        st.write(f"{payload.metrics.get('social_media_hours', 0):.1f} hours")
        
        st.write("**Charging Sessions**")
        st.write(f"{int(payload.metrics.get('charging_sessions', 0))} sessions")


def main() -> None:
    """Main Streamlit application."""
    
    # Configure page
    st.set_page_config(
        page_title="EcoPilot",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Title
    st.title("🌍 EcoPilot - Personal Carbon Intelligence")
    st.write("Understand your smartphone's carbon footprint and get personalized sustainability recommendations.")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    selected_persona = st.sidebar.selectbox(
        "Select Your Persona:",
        PERSONAS,
        help="Choose a persona that matches your smartphone usage pattern"
    )
    
    generate_report_button = st.sidebar.button(
        "🚀 Generate Report",
        use_container_width=True,
        type="primary",
    )
    
    # Add spacing and info
    st.sidebar.divider()
    st.sidebar.info(
        "**EcoPilot** analyzes your smartphone usage and estimates your daily carbon footprint. "
        "The report includes personalized recommendations and actionable implementation suggestions."
    )
    
    # Main content
    if generate_report_button:
        with st.spinner("🔄 Executing EcoPilot pipeline..."):
            pipeline_result = execute_ecopilot_pipeline(selected_persona)
        
        if pipeline_result:
            # Success message
            st.success(f"✅ Report generated for {selected_persona} persona")
            
            # Display metrics section
            st.divider()
            display_metrics_section(pipeline_result)
            
            # Display goal progress bar
            st.divider()
            display_goal_progress_bar(pipeline_result)
            
            # Display contributors section
            st.divider()
            display_contributors_section(pipeline_result)
            
            # Display coach section
            st.divider()
            display_coach_section(pipeline_result)
            
            # Display detailed metrics
            st.divider()
            display_metrics_detail_section(pipeline_result)
            
            # Footer
            st.divider()
            st.caption(
                "🌱 EcoPilot helps you understand and reduce your smartphone's carbon footprint. "
                "Every action counts! 💚"
            )
    else:
        # Initial welcome message
        st.info(
            "👋 Welcome to EcoPilot!\n\n"
            "1. Select a persona from the sidebar that matches your smartphone usage\n"
            "2. Click **Generate Report** to analyze your carbon footprint\n"
            "3. Review your insights and implementation suggestions\n"
            "4. Follow the coach's personalized recommendations\n\n"
            "Let's make a difference together! 🌍"
        )
        
        # Show persona descriptions
        st.subheader("📋 Persona Descriptions")
        
        personas_info = {
            "Student": "Moderate to heavy smartphone use with focus on social media and streaming.",
            "Office Worker": "Light to moderate use with balanced mix of work and entertainment.",
            "Heavy User": "Very high usage across all categories - streaming, social media, and charging.",
            "Minimal User": "Light usage with minimal streaming and social media activity.",
        }
        
        for persona, description in personas_info.items():
            st.write(f"**{persona}:** {description}")


if __name__ == "__main__":
    main()
