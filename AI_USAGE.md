# AI_USAGE.md

## AI Tools Used:
- ChatGPT 4o
- GitHub Copilot

## Effective Prompts:
- "I need to create a Python function that fetches weather data from NOAA API for multiple cities, handles rate limiting, implements exponential backoff for retries, and logs all errors. The function should return a pandas DataFrame with consistent column names regardless of the city."
- "I need to fix a Poetry PEP517 numpy build failure on Windows, including handling missing Visual C++ build tools and environment configuration."
- "I need to set the Python interpreter for a Poetry environment, and configure it to use a specific Python version."
- "I’m facing a Poetry virtualenv conflict — I need to remove the existing virtualenv and recreate a clean one bound to a specific Python version."
- "I’m getting a Windows pip OSError: [WinError 32] process cannot access the file — I need a fix for resolving this file lock issue during installation."
- "In my Streamlit visualization, Chicago isn't appearing — help me debug why it's missing from the data or visualization."
- "I need to refactor my Streamlit app.py file to fix a bug where city filtering is failing due to an incorrect mapping between timezone and city."
- "I need to fix a KeyError 'date' in an ETL script when the CSV only has a 'period' column, and safely fall back to 'period' if 'date' is missing."
- "I want to add a data freshness banner to my Streamlit dashboard that shows the most recent data date after applying filters."
- "I need to refactor my Streamlit app's date range filter logic to properly handle NaT values or empty dates without crashing."
- "I'm getting a Streamlit date input error when no valid dates are available — I need a fix to gracefully handle this scenario."
- "I need to rewrite my correlation_plot function to compute R² values for each city and display contextual interpretation messages inline on the dashboard."
- "I need to switch my correlation analysis from using R² to Pearson R, and update the dashboard to reflect this, including per-city and global interpretations."
- "I need to add per-city Pearson R values and a global Pearson R interpretation to my Streamlit dashboard, with color-coded alerts based on correlation strength."
- "Why is my global Pearson R weak even though some cities have strong R values? I need to understand this discrepancy and how it's computed."
- "I need a clear explanation of how Pearson correlation is calculated globally versus per city in a multi-location dataset."
- "Would it be better to use a weighted average or Fisher Z transform to combine correlation coefficients from multiple cities into a single global metric?"
- "I need to add visualizations to display regional variations in correlation strength across cities, and seasonal demand patterns over time."
- "I need to improve the visibility of weekend shading on my dual-axis time series charts by using colored vertical bands and adding a caption explaining the shaded areas."
- "I need to add a caption below the geographic map visualization in Streamlit clarifying what the color-coded markers (green, orange, red, gray) represent for energy demand levels."
- "I need to refine my app.py file to consistently add captions under each Plotly chart in Streamlit explaining what users are seeing — especially for maps and time series charts."
- "I need to fix a TypeError in my Streamlit app when summing nested outlier counts because some outlier entries are nested dictionaries."
- "I need to replace hardcoded color thresholds for energy demand (≤40MW = green, ≥80MW = red) with dynamic quantile-based classification using Q1 and Q3 from the data."

## AI Mistakes & Fixes:
- **Mistake:** AI code used wrong endpoint param.  
  **Fix:** Replaced `datatype` with `datatypeid` in NOAA API params.  
  **Lesson:** Always cross-verify API docs after AI code suggestions.

- **Mistake:** Initial suggestion to resolve `numpy` PEP517 build error didn’t account for missing C/C++ build tools on Windows.  
  **Fix:** Identified missing compilers and Visual Studio environment activation issue. Provided workaround to:
  1. Clean up Poetry virtualenvs.
  2. Manually set Python 3.11 interpreter for Poetry.
  3. Manually upgrade `pip`, `setuptools`, and `wheel` inside virtualenv before installing numpy.
  4. Clear temp `pip-unpack-*` folders causing `[WinError 32]` lock errors.  
  **Lesson:** Windows dev environments often require special care with compiled Python packages.

- **Mistake:** City filtering in dashboard was broken due to remapping `timezone → city`, which excluded valid cities like Chicago.  
  **Fix:** Refactored `app.py` to use the `city` column directly from the merged data instead of mapping based on timezone.  
  **Lesson:** Avoid unnecessary transformations when merged data already contains clean, structured fields.

- **Mistake:** ETL script dropped weather data with valid 'period' timestamps because 'date' column was missing.  
  **Fix:** Updated script to fall back to using `'period'` as the date if `'date'` is missing or null. Also preserves both fields.  
  **Lesson:** Never discard valid temporal data — fallback logic is critical when schema varies across sources.

- **Mistake:** AI-generated `correlation_plot` lacked inline R-squared interpretation.  
  **Fix:** Added logic to extract trendline fit results, compute R², and display correlation strength using Streamlit alerts.  
  **Lesson:** AI code often stops at visualization; adding business-contextual metrics improves dashboard value.

- **Mistake:** AI-suggested Streamlit date inputs failed when no valid dates existed in the dataset.  
  **Fix:** Added fallback logic in `app.py` to check for any valid dates before initializing date input widgets, with graceful errors if none found.  
  **Lesson:** Always defensively code against empty or NaT values in dashboards.

- **Mistake:** AI omitted data freshness display at the top of the dashboard.  
  **Fix:** Added latest data timestamp banner to dashboard after date filtering step.  
  **Lesson:** Business users expect clear currency indicators in operational dashboards.

- **Mistake:** AI initially computed R² globally, which obscured overall correlation strength.  
  **Fix:** Switched to **Pearson R** calculation globally and per city using `scipy.stats.pearsonr`. Added per-city R values and global R value to the dashboard with improved interpretative messages based on thresholds (`r ≥ 0.7` strong, `0.4 ≤ r < 0.7` moderate, `r < 0.4` weak).  
  **Lesson:** Global correlation metrics over mixed-population data can mask meaningful trends — always examine both aggregated and segmented stats.

- **Mistake:** AI didn’t originally account for **regional variations in correlation strength** across cities.  
  **Fix:** Added per-city Pearson R breakdown in dashboard, allowing decision-makers to observe local weather-energy dynamics.  
  **Lesson:** Regional patterns often differ in operational systems — avoid relying solely on global aggregates.

- **Mistake:** AI omitted **seasonal patterns in energy demand**.  
  **Fix:** Added monthly or seasonal trend visualizations to display average energy demand patterns over time.  
  **Lesson:** Energy systems naturally fluctuate by season — it’s essential to surface those patterns for planning and analysis.

- **Mistake:** Weekend shading on dual-axis time series was too subtle and lacked explanatory context.  
  **Fix:** Replaced light gray vertical bands with light red shading for weekends and added a caption beneath each chart clarifying that red bands indicate weekends.  
  **Lesson:** Visual cues should be immediately clear and labeled to avoid ambiguity in dashboards.

- **Mistake:** AI-generated geographic overview map lacked a clear caption explaining the meaning of color-coded markers for energy demand levels.  
  **Fix:** Added a caption directly beneath the map visualization in `app.py` describing the color codes: green for low, orange for moderate, red for high, and gray for missing data.  
  **Lesson:** Always accompany color-coded charts with explanatory legends or captions for accessibility and interpretability.

- **Mistake:** TypeError when summing outlier counts because some outlier entries were nested dictionaries.  
  **Fix:** Added a recursive sum helper function to `display_quality_report` that safely sums numeric counts within nested dictionaries before displaying total outliers.  
  **Lesson:** Always validate data structure before aggregation; nested dicts require recursive handling to aggregate counts correctly.

- **Mistake:** Color classification logic for energy demand used fixed thresholds (≤40 = green, ≥80 = red), which were inaccurate given actual energy values ranged in millions of MWh.  
  **Fix:** Replaced fixed thresholds with dynamic quantile-based classification using Q1 and Q3 of the `energy_demand_MW` values:
```python
q1 = df["energy_demand_MW"].quantile(0.25)
q3 = df["energy_demand_MW"].quantile(0.75)
def get_color(demand):
    if pd.isna(demand):
        return 'gray'
    elif demand <= q1:
        return 'green'
    elif demand >= q3:
        return 'red'
    else:
        return 'orange'
```


## Time Saved:
- **7 hours** on environment setup troubleshooting, pip/Poetry environment debugging, PEP517 build errors, and clean virtualenv recreation.
- **3 hours** debugging visualization errors and Streamlit filtering logic via AI-assisted refactoring.
- **1.5 hours** resolving data ingestion fallback for date/period inconsistencies in ETL.
- **1 hour** improving correlation visualization with R² and later Pearson R display and contextual messages.
- **45 minutes** refining correlation analysis logic and UI messaging for per-city and global Pearson R reporting.
- **40 minutes** implementing regional variation breakdown and seasonal demand trend visualizations.
- **30 minutes** streamlining dashboard UX by adding data freshness info, safe date handling, and improving weekend shading clarity.
- **25 minutes** clarifying color-coded map markers by adding caption explanations directly beneath geographic overview chart.
- **20 minutes** adapting color scale to quantile-based thresholds instead of absolute MW levels.
- **15 minutes** fixing nested dictionary summation error in outlier reporting with recursive sum logic.
