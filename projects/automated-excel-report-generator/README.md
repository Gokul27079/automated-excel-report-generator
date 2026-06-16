# ExcelFlow | Automated Excel Report Generator

An automated data pipeline and BI reporting web application that ingests raw sales data, cleans and processes it, runs analytical aggregations, and generates an enterprise-grade, beautifully formatted multi-sheet Excel workbook with embedded charts.

Designed as a modern tool for **Data Engineers**, **BI Analysts**, and **Python Developers** to automate manual spreadsheet operations.

## 🚀 Key Features

- **Ingestion Pipeline**: Upload any raw sales CSV file. Built-in header normalization maps variations (e.g., `sales`, `amount` ➜ `Revenue`).
- **Automated Data Cleaning**:
  - Automatically identifies and drops rows with missing key identifiers (Order ID) or critical values (Revenue).
  - Automatically filters duplicate transactions (keeping first occurrences).
  - Normalizes text casings (Title Case) and strips surrounding whitespace.
  - Automatically parses date strings of varying formats into proper dates.
- **Aggregations & Analytics**:
  - Computes core KPIs: Total Revenue, Total Orders, Average Order Value (AOV), and Data Quality Retention Rate.
  - Generates top products by revenue (Top 10), monthly sales trends, and regional breakdown.
- **Enterprise-Grade Excel Generation (`openpyxl` & `Matplotlib`)**:
  - **Sheet 1 — Raw Data**: Original dataset, styled header, auto-fit columns.
  - **Sheet 2 — Cleaned Data**: Polish dataset, formatted date, styled header.
  - **Sheet 3 — Summary Report**: Side-by-side KPI cards and summary tables styled in corporate slate-blue, incorporating native Excel formulas (`SUM`) for totals.
  - **Sheet 4 — Charts**: Embeds publication-quality charts (Top Products, Monthly Trend, Regional Share) directly in the sheet.
- **FastAPI REST API**: Serves JSON dashboard data, handles CSV uploads, and serves Excel document downloads.
- **Production-Grade UI Dashboard**: Built with a sleek dark slate glassmorphism theme, interactive charts (Chart.js), responsive styling, and **browser-based cache** (`localStorage`) to retain uploaded analysis state across reloads.

---

## 🛠️ Tech Stack

- **Backend Logic**: Python 3.10+, Pandas, NumPy, openpyxl, Matplotlib
- **API Server**: FastAPI, Uvicorn, python-multipart
- **Frontend Dashboard**: HTML5, Vanilla CSS3 (Custom gradients, HSL color tokens, animations), Vanilla JavaScript (ES6)
- **Charts & Icons**: Chart.js (CDN), FontAwesome (CDN)

---

## 📁 Repository Structure

```
automated-excel-report-generator/
├── data/
│   └── sales_data.csv          (messy raw input)
├── output/
│   ├── charts/                 (generated dashboard PNGs)
│   │   ├── monthly_trend.png
│   │   ├── regional_share.png
│   │   └── top_products.png
│   └── sales_report_June2026.xlsx  (final styled excel report)
├── src/
│   ├── static/                 (UI dashboard files)
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   ├── ingest.py               (data ingestion)
│   ├── clean.py                (cleaning logic)
│   ├── analyze.py              (groupby/aggregations)
│   ├── report.py               (excel styling & matplotlib embedding)
│   ├── mock_data.py            (messy synthetic data generator)
│   ├── api.py                  (FastAPI REST server & routers)
│   └── main.py                 (CLI orchestrator)
├── requirements.txt
└── README.md
```

---

## ⚙️ How to Setup and Run

### 1. Install Dependencies
Make sure Python is installed. Clone the repository and run:
```bash
pip install -r requirements.txt
```

### 2. Run the Command Line Interface (CLI)
You can run the full pipeline locally with one command. If you don't have a dataset, it will auto-generate a messy mock dataset in `data/sales_data.csv`:
```bash
python src/main.py
```
This output is saved to `output/sales_report_June2026.xlsx`. You can specify custom inputs:
```bash
python src/main.py --input path/to/your/file.csv --output path/to/report.xlsx
```

### 3. Run the Web Dashboard Server (API + UI)
Launch the FastAPI development server:
```bash
python -m uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```
Then, open your browser and navigate to:
```
http://localhost:8000
```

---

## 📊 Sample Output (Excel Details)

- **KPI Row**: Dynamic formatting (e.g., `$245,600.00` for Revenue and AOV, `#,##0` for Order Counts).
- **Summary Formulas**: Rather than hardcoding summary values, the sheet writes actual formulas (e.g., `=SUM(C8:C17)`) so the spreadsheet remains interactive when opened by end-users.
- **Embedded Charts**: Matplotlib figures are configured headlessly and saved at 150 DPI directly inside Excel, avoiding Excel default charting issues.

---

## 💡 Key Learnings & Engineering Patterns

1. **Robust Data Ingestion Mapping**: User-uploaded data can vary. Mapping key columns using aliases (lower casing, stripping spaces, matching standard patterns) prevents system crashes.
2. **Headless Visualization Execution**: Using `matplotlib.use('Agg')` is critical in web-servers. Without it, Matplotlib tries to launch GUI windows, causing background server processes to freeze.
3. **Double Bottom Borders**: Utilizing `openpyxl.styles.Side` styles like `double` for summary total rows mimics standard GAAP/Accounting presentation styles.
4. **Browser Cache Syncing**: Caching dashboard data in `localStorage` allows a clean user experience where state persists on page refreshes, reducing API roundtrips.
