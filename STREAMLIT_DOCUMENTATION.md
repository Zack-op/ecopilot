# EcoPilot Streamlit UI - Documentation

## Overview

The EcoPilot Streamlit application provides a clean, user-friendly interface for analyzing smartphone carbon footprints. It completely reuses the existing backend pipeline without any modifications.

**Status:** ✅ Production Ready

---

## Running the Application

### Prerequisites

Install Streamlit if not already installed:
```bash
pip install streamlit
```

### Launch the App

From the EcoPilot project root directory:

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501` in your default browser.

---

## Application Features

### 1. **Title & Description**
- **Title:** 🌍 EcoPilot - Personal Carbon Intelligence
- **Subtitle:** Understand your smartphone's carbon footprint and get personalized sustainability recommendations.

### 2. **Sidebar Configuration**

#### Persona Selector
Dropdown to choose from 4 personas:
- **Student:** Moderate to heavy smartphone use with focus on social media and streaming
- **Office Worker:** Light to moderate use with balanced mix of work and entertainment
- **Heavy User:** Very high usage across all categories
- **Minimal User:** Light usage with minimal streaming and social media

#### Generate Report Button
Primary action button that executes the EcoPilot pipeline for the selected persona.

#### Information Panel
Sidebar info box explaining the app's purpose and functionality.

### 3. **Display Sections** (After Report Generation)

#### Key Metrics (4-Column Display)
Using Streamlit's metric component for consistent styling:
- **💨 Carbon Footprint** - In grams (g CO2) with delta indicator
- **⚡ Energy Usage** - In kilowatt-hours (kWh)
- **🎯 Goal Progress** - As percentage of daily target
- **📊 Status** - Current progress status (e.g., "On Target")

#### Goal Progress Bar
Visual progress bar showing goal achievement percentage with label.

#### Major Contributors Section
Using Streamlit expanders for each contributor:
- Expandable cards showing rank and contributor category
- First contributor expanded by default
- Each expander contains:
  - **Reason:** Why this is a major contributor
  - **Action:** Recommended action to reduce impact
  - **Ways to achieve this:** 2-3 implementation suggestions (LLM-generated)

#### AI Sustainability Coach Section
Bordered container displaying the LLM coach's personalized message about overall footprint and recommendations.

#### Smartphone Usage Metrics
Two-column layout showing detailed breakdown:
- Screen Time (hours)
- Video Streaming (hours)
- Music Streaming (hours)
- Social Media (hours)
- Charging Sessions (count)

#### Footer
Motivational caption emphasizing the importance of sustainability actions.

### 4. **Welcome Screen** (Initial State)
Before any report is generated:
- Welcome message with step-by-step instructions
- Persona descriptions to help users choose
- Prompts user to select persona and generate report

---

## Backend Integration

### Reused Functions (No Modifications)

The Streamlit app completely reuses these backend functions:

```python
# From core/smartphone_simulator.py
generate_smartphone_payload(user_id, persona, rng)

# From core/telemetry_parser.py
validate_payload(raw_payload)

# From core/climatiq_provider.py
ClimatiqProvider.calculate(payload)

# From core/insight_generator.py
generate_insights(metrics, carbon_result)

# From core/goal_tracker.py
track_goal(daily_co2_kg, target_co2_kg)

# From core/llm_insight_generator.py
LLMInsightGenerator.generate(carbon_result, insights, goal)
LLMInsightGenerator.generate_implementation_suggestions(insights)
```

### Pipeline Execution

The `execute_ecopilot_pipeline()` function:
1. Generates smartphone telemetry for selected persona
2. Validates telemetry payload
3. Calculates carbon emissions
4. Generates insights (contributors + rankings)
5. Tracks goal progress
6. Generates coach message
7. Generates implementation suggestions

---

## Code Structure

### Main Functions

#### `execute_ecopilot_pipeline(persona: str) -> Dict[str, Any] | None`
Executes the complete EcoPilot pipeline and returns results or None on error.

**Parameters:**
- `persona`: The selected persona name

**Returns:**
- Dictionary with pipeline results or None if execution fails

**Error Handling:**
- Validates telemetry payload
- Checks Climatiq API key availability
- Provides fallback calculations if API unavailable
- Returns None with error message on failure

#### `display_metrics_section(pipeline_result)`
Displays carbon footprint, energy usage, goal progress, and status in a 4-column metric display.

#### `display_goal_progress_bar(pipeline_result)`
Shows visual progress bar for goal achievement.

#### `display_contributors_section(pipeline_result)`
Displays each contributor in an expandable expander with:
- Reason for contribution
- Recommended action
- Implementation suggestions (if available)

#### `display_coach_section(pipeline_result)`
Shows the AI coach's personalized message in a bordered container.

#### `display_metrics_detail_section(pipeline_result)`
Displays detailed smartphone usage metrics in a 2-column layout.

#### `format_carbon_display(co2_kg: float) -> tuple[float, str]`
Helper to convert CO2 from kg to grams and format for display.

#### `main()`
Main Streamlit application entry point.

---

## Configuration Constants

```python
DAILY_TARGET_CO2_KG = 0.0150  # Daily target in kg (15 grams)
PERSONAS = ["Student", "Office Worker", "Heavy User", "Minimal User"]
PERSONA_USER_IDS = {
    "Student": "student",
    "Office Worker": "office_worker",
    "Heavy User": "heavy_user",
    "Minimal User": "minimal_user",
}
```

---

## Example User Flows

### Flow 1: Student Persona
1. User opens app (welcome screen displayed)
2. Sidebar has "Student" pre-selected
3. User clicks "🚀 Generate Report"
4. App executes pipeline
5. Report shows:
   - Carbon Footprint: ~18-25 g CO2
   - Energy Usage: ~0.08-0.12 kWh
   - 2-3 major contributors (video streaming, social media, screen time)
   - Coach message and implementation suggestions

### Flow 2: Heavy User Persona
1. User selects "Heavy User" from dropdown
2. Clicks "🚀 Generate Report"
3. Report shows:
   - Carbon Footprint: ~30-40 g CO2
   - Energy Usage: ~0.15-0.25 kWh
   - 3-4 major contributors with high impact
   - More aggressive recommendations from coach

### Flow 3: Re-generate for Different Persona
1. User changes persona dropdown
2. Clicks "🚀 Generate Report" again
3. App generates new report for the selected persona
4. Previous report is replaced

---

## Error Handling

### CLIMATIQ_API_KEY Not Configured
```
⚠️ CLIMATIQ_API_KEY not configured. Using fallback calculations.
```
- App continues with synthetic carbon calculations
- Demonstrates all features without real API

### Telemetry Validation Failure
```
❌ Telemetry validation failed: [error message]
```
- Error displayed in red banner
- User can try again with different persona

### Carbon Calculation Failure
```
❌ Carbon calculation failed: [error message]
```
- Explains what went wrong
- User can retry

### Exception Handling
```
❌ Pipeline execution error: [error details]
```
- Catches and displays unexpected errors
- Prevents app crash

---

## Styling & UI Components

### Colors & Emojis
- 🌍 Earth emoji for main title
- 💨 Carbon footprint metric
- ⚡ Energy usage metric
- 🎯 Goal progress metric
- 📊 Status metric
- 🔍 Major contributors section
- 🤖 AI Coach section
- 📱 Usage metrics section
- 🌱 Motivational footer emoji

### Streamlit Components Used
- `st.set_page_config()` - Configure page layout and theme
- `st.title()` - Main title
- `st.write()` - Text and descriptions
- `st.sidebar.*` - Sidebar elements
- `st.selectbox()` - Persona selector
- `st.button()` - Generate Report button
- `st.spinner()` - Loading indicator
- `st.success()` - Success message
- `st.error()` - Error messages
- `st.info()` - Information boxes
- `st.metric()` - Key metrics display
- `st.progress()` - Progress bar
- `st.expander()` - Collapsible contributor cards
- `st.container()` - Bordered coach message
- `st.divider()` - Visual separators
- `st.columns()` - Layout columns
- `st.caption()` - Footer text

---

## Performance Considerations

### Pipeline Execution
- Non-deterministic random seed (new metrics each run)
- Execution typically takes 2-5 seconds (depending on Climatiq API)
- Loading spinner indicates ongoing processing

### State Management
- No session state persistence
- Each report generation is independent
- Refreshing browser clears all data

---

## Browser Compatibility

- Chrome, Firefox, Safari (latest versions)
- Desktop and tablet friendly
- Mobile support available (condensed layout)

---

## Known Limitations

1. **No Persistence:** Reports are not saved (stateless app)
2. **No Authentication:** Anyone with access to the URL can use it
3. **Random Metrics:** Each generation produces different results (realistic simulation)
4. **Climatiq Dependency:** Requires valid API key for real carbon calculations
5. **No Database:** All calculations are ephemeral

---

## Deployment Options

### Local Development
```bash
streamlit run streamlit_app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Deploy via Streamlit Cloud dashboard
3. Set `CLIMATIQ_API_KEY` environment variable in secrets

### Docker
```bash
docker build -t ecopilot-ui .
docker run -p 8501:8501 -e CLIMATIQ_API_KEY=xxx ecopilot-ui
```

### Other Platforms
- Heroku
- AWS EC2
- Azure App Service
- Google Cloud Run

---

## Future Enhancements (Not in Scope)

- User authentication
- Report history/persistence
- Persona customization
- Additional metrics (water usage, battery health)
- Comparison with other users (anonymized)
- Export reports as PDF
- Integration with phone APIs
- Real telemetry data collection
- Gamification (badges, leaderboards)
- Multi-language support

---

## Testing the App

### Manual Testing Checklist

#### Sidebar
- [ ] All personas appear in dropdown
- [ ] "Student" is pre-selected
- [ ] Button text says "🚀 Generate Report"
- [ ] Info box displays correctly

#### Initial Screen
- [ ] Welcome message appears
- [ ] Persona descriptions show
- [ ] No report content visible

#### Report Generation
- [ ] Click button triggers execution
- [ ] Loading spinner appears
- [ ] Success message displays
- [ ] All sections render correctly

#### Metrics Display
- [ ] 4 metrics visible (Carbon, Energy, Goal, Status)
- [ ] Values are numeric and reasonable
- [ ] Delta indicators show

#### Goal Progress Bar
- [ ] Displays percentage
- [ ] Visual fill matches percentage

#### Contributors Section
- [ ] All contributors listed
- [ ] Expandable cards work
- [ ] First expanded by default
- [ ] Suggestions display correctly

#### Coach Section
- [ ] Message displays in bordered container
- [ ] Text is readable

#### Usage Metrics
- [ ] 5 metrics shown (screen, video, music, social, charging)
- [ ] Values realistic for persona

#### Different Personas
- [ ] Each generates different values
- [ ] Heavy User has higher metrics than Minimal User
- [ ] Reports are logically distinct

### Automated Testing

```python
# Example pytest test
def test_execute_ecopilot_pipeline():
    result = execute_ecopilot_pipeline("Student")
    assert result is not None
    assert "carbon_result" in result
    assert "insights" in result
    assert "goal" in result
```

---

## Troubleshooting

### App won't start
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Check Python version (3.8+)
python --version
```

### Metrics show 0 or no data
- Ensure EcoPilot backend modules are in PYTHONPATH
- Check imports in streamlit_app.py

### Climatiq API errors
- Set CLIMATIQ_API_KEY environment variable
- App will use fallback calculations if key missing

### Performance issues
- Reduce persona complexity
- Check internet connection (Climatiq API calls)
- Run on local machine instead of shared server

---

## Summary

✅ **Production-Ready Streamlit UI for EcoPilot**

- Clean, intuitive interface
- Completely reuses backend (no modifications)
- Full error handling and fallbacks
- Suitable for hackathon demo
- Easily deployable
- No authentication or persistence overhead

**Status:** READY FOR DEPLOYMENT 🚀

---

**Last Updated:** Session Complete
**Version:** 1.0
