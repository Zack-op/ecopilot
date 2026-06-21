# EcoPilot Streamlit UI - Quick Start Guide

## 30-Second Setup

```bash
# 1. Ensure you're in the EcoPilot project directory
cd d:\ecopilot

# 2. Install Streamlit (if not already installed)
pip install streamlit

# 3. Run the app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

---

## What You'll See

### 1. Welcome Screen (Initial)
```
🌍 EcoPilot - Personal Carbon Intelligence

Understand your smartphone's carbon footprint...

👋 Welcome to EcoPilot!

1. Select a persona from the sidebar...
2. Click Generate Report...
3. Review your insights...
4. Follow the coach's recommendations...

📋 Persona Descriptions
Student: Moderate to heavy smartphone use...
Office Worker: Light to moderate use...
Heavy User: Very high usage...
Minimal User: Light usage...
```

### 2. Sidebar
```
⚙️ Configuration

Select Your Persona:
[Dropdown: Student ▼]

[🚀 Generate Report]

(Divider)

ℹ️ EcoPilot analyzes your smartphone usage...
```

### 3. After Clicking "Generate Report"
The app displays (in sequence):

#### ✅ Success Message
```
Report generated for Student persona
```

#### 📊 Key Metrics (4-column display)
```
💨 Carbon Footprint    ⚡ Energy Usage    🎯 Goal Progress    📊 Status
18.5 g CO2            0.0852 kWh         62.3%               On Target
```

#### 📈 Goal Progress Bar
```
Goal Progress: 62.3% [████████░░░░░░░░░░░░]
```

#### 🔍 Major Contributors
```
1. Video Streaming
  Reason: Video streaming was a major contributor...
  Action: Reduce video streaming by 30 minutes daily.
  Ways to achieve this:
  • Watch one fewer episode per day.
  • Set a fixed viewing window for streaming.
  • Replace streaming time with offline activities.

2. Social Media
  Reason: Social media usage was a notable part...
  [Click to expand]
```

#### 🤖 AI Sustainability Coach
```
┌─────────────────────────────────────┐
│ Your daily carbon footprint is ...  │
│                                     │
│ Your top contributors are...        │
└─────────────────────────────────────┘
```

#### 📱 Smartphone Usage Metrics
```
Screen Time              Social Media
6.4 hours              2.1 hours

Video Streaming         Charging Sessions
2.3 hours              2 sessions

Music Streaming
1.8 hours
```

---

## Features Explained

### Persona Selection
Four personas with different smartphone usage patterns:

| Persona | Usage Level | Typical Carbon |
|---------|-------------|---|
| Student | Moderate-High | 18-25g CO2 |
| Office Worker | Light-Moderate | 10-15g CO2 |
| Heavy User | Very High | 30-40g CO2 |
| Minimal User | Light | 5-8g CO2 |

### Metrics Explained

- **Carbon Footprint:** Estimated daily CO2 from smartphone usage (in grams)
- **Energy Usage:** Estimated daily energy consumption (in kilowatt-hours)
- **Goal Progress:** How close you are to the 15g daily target (100% = on target)
- **Status:** Whether you're "On Target", "Above Target", or "Exceeding Target"

### Contributors

Each contributor shows:
1. **Rank:** Priority by impact (1 = highest impact)
2. **Reason:** Why this is a top contributor
3. **Action:** Specific recommendation to reduce impact
4. **Ways to Achieve:** 2-3 practical implementation ideas

### Coach Message

AI-generated personalized message that:
- Summarizes your overall footprint
- Highlights top contributors
- Provides encouragement
- Suggests next steps

---

## Try It Out!

### Scenario 1: Heavy User
1. Select "Heavy User" from sidebar
2. Click "Generate Report"
3. Notice: Higher carbon footprint, more contributors, more aggressive recommendations

### Scenario 2: Compare Personas
1. Generate report for "Heavy User"
2. Change dropdown to "Minimal User"
3. Click "Generate Report" again
4. Notice the dramatic difference in footprints

### Scenario 3: Fresh Generation
1. Keep same persona selected
2. Click "Generate Report" again
3. Notice: Metrics change (realistic randomized simulation)

---

## What's Happening Behind the Scenes

```
Generate Report Click
        ↓
Simulate smartphone telemetry
        ↓
Validate telemetry data
        ↓
Calculate carbon emissions (via Climatiq API)
        ↓
Analyze metrics for contributors
        ↓
Track progress against daily target
        ↓
Generate AI coach message
        ↓
Generate implementation suggestions
        ↓
Display everything in Streamlit UI
```

---

## Customization

### Change Default Persona
Edit line 88 in `streamlit_app.py`:
```python
selected_persona = st.sidebar.selectbox(
    "Select Your Persona:",
    PERSONAS,
    index=2,  # Change to Heavy User by default (was 0 for Student)
)
```

### Change Daily Target
Edit line 25:
```python
DAILY_TARGET_CO2_KG = 0.010  # 10 grams instead of 15
```

### Add New Persona
Requires backend changes (not in this app's scope).

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit
```

### "CLIMATIQ_API_KEY not configured"
```
The app still works with fallback calculations.
To use real data, set environment variable:
set CLIMATIQ_API_KEY=your_key_here
```

### App crashes on "Generate Report"
1. Check Python version: `python --version` (need 3.8+)
2. Check imports are correct in core/ directory
3. Ensure working directory is d:\ecopilot

### Metrics show 0 or strange values
- Refresh page (Cmd+Shift+R or Ctrl+Shift+R)
- Try different persona
- Check console output for errors

---

## Tips for Demo/Presentation

1. **Pre-load the app** before presenting
2. **Use "Heavy User"** for most dramatic results
3. **Generate 2-3 times** to show different metrics each time
4. **Expand only first contributor** to save time
5. **Highlight the suggestions** (most interesting to users)
6. **Mention the AI Coach** (shows intelligence of system)

---

## Production Readiness Checklist

✅ Clean, intuitive UI
✅ All backend functions reused (no duplication)
✅ Error handling for API failures
✅ Fallback calculations available
✅ No authentication required
✅ No database needed
✅ Single-file application
✅ Type hints maintained
✅ Comprehensive documentation
✅ Ready for deployment

---

## Next Steps

1. **Run the app:** `streamlit run streamlit_app.py`
2. **Test different personas**
3. **Review contributor suggestions**
4. **Check AI coach messages**
5. **Share with team/stakeholders**
6. **Deploy to Streamlit Cloud** (optional)

---

## Need Help?

See `STREAMLIT_DOCUMENTATION.md` for:
- Complete feature documentation
- Deployment options
- Code structure details
- Testing guidelines
- Troubleshooting section

---

**Status:** ✅ READY TO LAUNCH 🚀

Enjoy EcoPilot!
