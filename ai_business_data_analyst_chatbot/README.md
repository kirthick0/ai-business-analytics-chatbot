# AI Business Data Analyst Chatbot

A Streamlit business analytics application for CSV/Excel uploads. Explore data quality, run descriptive analysis, ask plain-language questions, build interactive charts, try suitable machine-learning models, and download CSV/PDF reports. Pandas computes supported dataset answers locally; GPT-4.1 mini explains results and answers general business/data questions.

## Features

- Dashboard cards for rows, columns, missing cells, duplicates, and detected revenue/sales.
- CSV, XLS, and XLSX file upload; sample sales dataset included.
- Explicit data-cleaning options that preserve the original upload.
- Session-local SQLite snapshot of the uploaded data.
- GPT business analyst for general questions about analytics, Python, SQL, Excel, Power BI, cleaning, EDA, statistics, ML, finance, marketing, KPIs, reporting, and dashboards.
- Deterministic Pandas answers for totals, averages, rankings, category summaries, monthly trends, record counts, missing values, and correlations.
- GPT explanations of dataset results are opt-in. The application sends a compact computed summary and column schema, not raw dataset rows; summaries can include category labels.
- Descriptive statistics, IQR outlier review, correlation heatmap, and Plotly bar/line/pie/scatter/histogram charts.
- Optional linear regression, random-forest regression/classification, and K-Means clustering when the data is suitable.
- Business findings with CSV exports and PDF report containing a data-derived chart when suitable.
- Light/dark appearance and responsive layout.

## Project structure

```text
app.py
requirements.txt
README.md
sample_sales.csv
modules/
  data_loader.py
  data_cleaning.py
  data_analysis.py
  chatbot.py
  openai_assistant.py
  visualization.py
  machine_learning.py
  business_insights.py
  report_generator.py
assets/style.css
data/.gitkeep
tests/
```

## Windows PowerShell setup

Open the project folder in VS Code, then open **Terminal → New Terminal**. From the project root, run:

```powershell
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

If `.venv` does not exist, create it first with `py -3.13 -m venv .venv`, then run the installation commands above. If you already created the environment, do not recreate it. The app opens at **http://localhost:8501**; if it does not open automatically, copy that address into your browser.

Edit `.env` and set your OpenAI key:

```env
OPENAI_API_KEY=your_real_api_key
OPENAI_MODEL=gpt-4.1-mini
```

`.env` is ignored by Git. Never commit or share the real key. `OPENAI_MODEL` is optional and can be changed to another model enabled for your OpenAI account.

To activate the environment in PowerShell instead, use `.\.venv\Scripts\Activate.ps1`. If activation is blocked by policy, the commands using the explicit `.venv` Python path above avoid activation.

## First demo

1. Start the app using the command above.
2. Select **Load included sample sales data** in the sidebar, or upload your own CSV/Excel workbook.
3. Use **Dashboard** to review dataset totals and quality.
4. Open **AI analyst**, ask “Which product generates the highest sales?” or “What is the monthly sales growth?”, then inspect the computed table and chart.
5. Explore **Automated analysis**, **Visualizations**, and **Machine learning**.
6. Open **Business insights & reports** to download a PDF or export the latest model result.

## Example analyst questions

- What is the total revenue?
- Which product generates the highest sales?
- Which region has the highest profit?
- Show the top 10 customers by revenue.
- What is the monthly sales growth?
- Show average profit by category.
- How many records are in the dataset?
- Which columns have missing values?
- Show the correlation between the numeric measures.

Use the exact column names shown on the dashboard for the most reliable interpretation. The built-in analyst supports common measure/grouping language, not unrestricted conversational reasoning; when it cannot identify a relevant numeric column, it explains what is missing instead of making up a number.

## Data, privacy, and limitations

- Dataset loading and calculations run locally in the Streamlit session. General GPT questions send the prompt and limited chat history to OpenAI. Dataset rows are not sent; if you enable dataset-result explanations, the app sends the question, column names/types, basic quality facts, and a compact calculated summary. Such summaries can contain category/customer labels, so do not enable sharing for sensitive data.
- The application requires an OpenAI API key for GPT answers. Supported deterministic dataset calculations remain available without a key.
- The SQLite database is in memory and is recreated when a session loads a dataset. It is not a permanent database.
- Uploaded data is not persisted by this project, but Streamlit's hosting environment may have its own logging/storage behavior. Avoid confidential or personally identifiable information on untrusted hosts.
- Cleaning changes are opt-in and applied to an analysis copy; the original upload stays intact.
- Machine-learning evaluation is exploratory. Small, biased, or time-dependent datasets may produce unreliable scores; a random train/test split is not a substitute for time-series validation.
- Monthly growth is calculated as percentage change from the previous observed month; no causal explanation is inferred.
- PDF reports include a chart only when a category and numeric column can be charted.

## Troubleshooting

- **Missing module:** run `& .\.venv\Scripts\python.exe -m pip install -r requirements.txt` from the project root.
- **Missing API key:** set `OPENAI_API_KEY` in `.env`, or configure it in Streamlit Secrets when deployed. Do not put a real key in source code or `.env.example`.
- **Invalid key / quota / rate limit:** confirm the key is active and the OpenAI account has API billing/credits; retry after a rate limit.
- **Port 8501 already in use:** close the other Streamlit process or use `& .\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502` and open `http://localhost:8502`.
- **Excel import error:** ensure the workbook is a valid `.xlsx`/`.xls` file; both readers are listed in requirements.
- **Upload too large:** uploads are limited to 50 MB. Reduce the file size or split the workbook/CSV.
- **A question is not understood:** check the detected numeric/categorical columns and ask for an available measure by its exact column name.

## Streamlit Community Cloud deployment

1. Push the project (without `.env`, `.venv`, or real credentials) to a GitHub repository.
2. In Streamlit Community Cloud, create an app from the repository and set `app.py` as the entry point.
3. In the app's **Settings → Secrets**, add:

   ```toml
   OPENAI_API_KEY = "your_real_api_key"
   OPENAI_MODEL = "gpt-4.1-mini"
   ```

4. Deploy. Streamlit installs the dependencies from `requirements.txt`; the app reads the key from Streamlit Secrets without exposing it in the UI.

Run locally with `streamlit run app.py` after installing requirements and configuring `.env`.

## Project presentation summary

“This business analytics dashboard is built with Python and Streamlit. Pandas loads, profiles, and calculates dataset answers locally; GPT-4.1 mini provides conversational explanations and general analytics guidance. SQLite stores an in-memory session snapshot, Plotly provides interactive charts, scikit-learn supplies optional supervised and unsupervised models, and ReportLab generates downloadable PDF reports. Dataset-derived summaries are shared with OpenAI only when explicitly enabled in the chat.”
