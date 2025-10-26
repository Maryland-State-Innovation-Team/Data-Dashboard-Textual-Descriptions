# Data-Dashboard-Textual-Descriptions

Proof of concept for prerendering AI-generated textual descriptions of visual data-driven media.

---

## Setup Instructions

### 1. Python Virtual Environment (Windows)

Open a terminal (e.g., Command Prompt or PowerShell) in the project directory and run:

```sh
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and add your [Gemini API key](https://aistudio.google.com/app/apikey):

```sh
copy .env-example .env
```

Edit `.env` and set:

```
GEMINI_API_KEY=your-gemini-api-key-here
```

---

## Project Structure and Main Files

### `html/index.html`

- The main interactive dashboard.
- Uses [Tailwind CSS](https://tailwindcss.com/) and [Plotly.js](https://plotly.com/javascript/) for styling and charting.
- Loads data from `9qyj-bhez.json` and AI-generated insights from `aiInsights.json` (if available).
- Provides dropdowns to select agricultural practices and counties, displays a chart, a data table, and AI-generated Q&A insights.

### `take_screenshots.py`

- Starts a local HTTP server to serve the `html` directory.
- Uses Selenium (headless Chrome) to automate the browser, iterating through all combinations of dropdown options in `index.html`.
- Captures a PNG screenshot for each combination and saves them to the `screenshots` folder.
- Useful for generating a dataset of chart images for further analysis or AI processing.

### `generate_accessibility_insights.py`

- Processes all PNG images in the `screenshots` folder.
- For each image, sends it to the Gemini 2.5 Flash model with a prompt to generate accessibility-focused question-and-answer pairs.
- Stores the results in `html/aiInsights.json`, keyed by the screenshot filename.
- Designed to help users with visual impairments by providing high-level, synthesized textual insights about each chart.

---

## Typical Workflow

1. **Prepare Data:** Ensure `html/index.html` and `9qyj-bhez.json` are ready.
2. **Take Screenshots:**  
   Run `python take_screenshots.py` to generate chart images for all dropdown combinations.
3. **Generate AI Insights:**  
   Run `python generate_accessibility_insights.py` to create `aiInsights.json` with accessibility Q&A for each chart.
4. **View Dashboard:**  
   Open `html/index.html` in a browser. The dashboard will display charts, data tables, and AI-generated insights for each selection.

---

## Notes

- Requires Chrome and [ChromeDriver](https://chromedriver.chromium.org/) for Selenium automation.
- The Gemini API key is required for generating AI insights.
- If `aiInsights.json` is missing, the dashboard will hide the AI insights section.

---
