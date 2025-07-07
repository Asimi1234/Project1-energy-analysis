# Project Presentation Video

[Link to Video Presentation](http://example.com/link-to-your-video)

# 📽️ Project 1: Energy Demand & Weather Correlation — Video Script

## 🎙️ 0:00–0:30 — Problem Statement & Business Value

Hi, I'm **Israel Asimi**.  
Energy companies lose **millions of dollars annually** due to inaccurate demand forecasting. These errors lead to **overproduction**, **blackouts**, and **higher operational costs**.

This project addresses that challenge by integrating **historical and real-time weather data** with **regional electricity demand** to improve forecasting accuracy — enabling smarter grid operations and energy management decisions.

---

## 🎙️ 0:30–2:00 — Technical Walkthrough

**(Show your project architecture diagram or folder structure briefly)**

I built a **modular, production-ready data pipeline in Python** that fetches:
- **Daily weather data** from NOAA
- **Energy demand data** from the U.S. EIA  
for five U.S. cities.

Key pipeline features:
- **Automated error handling and logging**
- **Data freshness and outlier detection**
- **Config-driven architecture** for easy extension

**(Show a live API call or code snippet in terminal)**  
Here’s an example of the **data fetching function** with:
- Exponential backoff for API rate limits
- Error logging
- Fallback handling if an API is unavailable  

**(Show your data quality report dashboard tab)**  
After each run, a **data quality report** flags:
- Missing values
- Outliers (extreme temperatures and invalid demand)
- Data staleness  
to ensure reliable data for analysis.

**(Show each dashboard visualization one by one)**

The Streamlit dashboard includes:
- 🗺️ **Geographic Map:** Avg. demand (size) & avg. temperature (color)
- 📊 **Time Series:** Daily temp vs. energy demand (dual-axis) with weekends highlighted
- 📈 **Correlation Scatter:** Temp vs. demand with regression line and **Pearson R value**
- 🔍 **Per-City Correlation Panel:** R values for each city, categorized as **strong**, **moderate**, or **weak**
- 🔥 **Heatmap:** Energy demand by temperature band and day of week

I also added:
- 📊 **Regional Correlation Insights:** to highlight how cities like **Phoenix** exhibit strong weather-demand coupling while **Seattle** shows virtually none.
- 📅 **Seasonal Patterns Visuals:** that reveal consistent demand peaks in summer and dips in winter across most regions.

---

## 🎙️ 2:00–2:30 — Results & Insights

From this analysis:
- Confirmed a **strong correlation (R ≥ 0.7)** between temperature extremes and energy demand in most cities.
- Identified **weekday vs. weekend consumption patterns**
- Highlighted **unique regional differences** — for example, **Phoenix** showed an R of **0.927**, while **Seattle** had an R of **-0.049**
- Detected **seasonal energy usage patterns**, with demand typically peaking in **summer months**.

These insights help energy providers **optimize generation planning and demand response** strategies based on both **regional characteristics** and **seasonal cycles**.

---

## 🎙️ 2:30–3:00 — AI Collaboration & Learning

Throughout this project, I used **ChatGPT 4o** and **GitHub Copilot** for:
- API integration
- Data visualization debugging
- Environment setup and dependency troubleshooting
- Refining correlation analysis logic and dashboard messaging

### Example AI mistake:
- AI suggested a wrong NOAA API parameter — I fixed this by verifying against the official API docs.  
**Lesson:** Always cross-validate AI-generated code against documentation.

Another issue:  
- AI originally computed **R² globally**, which masked meaningful trends across cities. I switched to **Pearson R** and added per-city breakdowns for actionable insight.  
**Lesson:** Always validate whether aggregated metrics accurately reflect localized realities.

**Time saved:** ~**9 hours** through AI-assisted troubleshooting, analysis refinement, and dashboard development.

If I repeated this project, I'd implement **data schema validation earlier** to proactively manage schema inconsistencies.

---

## 📌 Close:
Thank you for watching — you’ll find my full project repo and AI usage documentation linked in the description.
