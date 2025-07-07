# AI_USAGE.md

## AI Tools Used:
- ChatGPT 4o
- GitHub Copilot

## Effective Prompts:
- "Write a Python function to fetch NOAA weather data with exponential backoff and logging."
- "How do I fix Poetry PEP517 numpy build failure on Windows?"
- "How to set Python interpreter for Poetry environment?"
- "Poetry virtualenv conflict — how to remove and recreate cleanly?"
- "Fix Windows pip OSError: [WinError 32] process cannot access the file"
- "Why can't I see Chicago in my visualization?"
- "Refactor my Streamlit app.py and fix the city filtering bug"
- "Fix KeyError 'date' in ETL script when only 'period' is available in CSV"
- "Add data freshness banner to Streamlit dashboard"
- "Refactor date range filter logic to handle NaT or empty dates in Streamlit app"
- "Fix Streamlit date input error when no valid dates available"
- "Rewrite correlation_plot function to display R² and interpret result inline"

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

## Time Saved:
- **7 hours** on environment setup troubleshooting, pip/Poetry environment debugging, PEP517 build errors, and clean virtualenv recreation.
- **3 hours** debugging visualization errors and Streamlit filtering logic via AI-assisted refactoring.
- **1.5 hours** resolving data ingestion fallback for date/period inconsistencies in ETL.
- **1 hour** improving correlation visualization with R² display and contextual messages.
- **30 minutes** streamlining dashboard UX by adding data freshness info and safe date handling.
