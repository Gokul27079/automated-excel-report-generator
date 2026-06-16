# SpendWise | AI-Powered Expense Tracker

SpendWise is a production-grade personal finance management and expense tracking application. It integrates a **FastAPI REST API**, an **SQLite database**, **openpyxl-based styled Excel reporting**, and a **gorgeous dark-mode dashboard UI** featuring interactive budget tracking gauges and data charts.

## 🚀 Key Features

- **Full CRUD Ledger**: Create, Read, Update, and Delete individual expenses with instant client-side updates.
- **Budget Tracking Gauge**: Set a monthly budget with an interactive input. Displays a dynamic progress bar that changes colors (Green ➜ Warning Orange ➜ Danger Red) as you approach your threshold.
- **Bulk CSV Data Uploader**: Import expenses in bulk by dragging and dropping a CSV file. The backend automatically parses and normalizes column headers (e.g. mapping `cost` or `price` ➜ `amount`).
- **Interactive Visualizations (Chart.js)**:
  - **Category Share Doughnut Chart**: Displays percentage share spent across food, utilities, housing, etc.
  - **Daily Spending Trend Line Chart**: Visualizes spending volume chronologically.
- **Styled Excel Reports (`openpyxl`)**:
  - **Sheet 1 — Expense Log**: List of all items, sorted chronologically, with dark-green accounting headers, currency formatting, and dynamic Excel formulas (`SUM(...)`).
  - **Sheet 2 — Category Breakdown**: Pivot summary showing category-wise totals and percentage shares.
  - **Sheet 3 — Dashboard**: Embeds publication-quality charts directly inside the workbook using PIL-based image anchors.
- **Browser-Based Local Storage Cache**:
  - Caches current expense datasets and summaries inside `localStorage` to enable instant dashboard loading on startup and provide offline view recovery.
  - Caches monthly budget settings across reloads.
- **Auto-Seeding**: Launches with a pre-configured realistic database of 30+ transactions on first-run.

---

## 🛠️ Tech Stack

- **Backend REST API**: Python 3.10+, FastAPI, Uvicorn, python-multipart
- **Database**: SQLite3, SQL row factory mapping
- **Excel Export Pipeline**: openpyxl, Matplotlib, Pandas, NumPy
- **Frontend UI Dashboard**: HTML5, Vanilla CSS3 (Custom gradients, glowing cards, keyframes), Vanilla JavaScript (ES6), Chart.js (CDN), FontAwesome (CDN)

---

## 📁 Repository Structure

```
expense-tracker/
├── expenses.db             (SQLite database file created on start)
├── output/                 (generated spreadsheet reports)
│   ├── temp_charts/        (temporary Matplotlib figures)
│   └── expense_report.xlsx (final formatted Excel export)
├── src/
│   ├── static/             (dashboard assets)
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   ├── database.py         (SQLite schema initialization & SQL helpers)
│   ├── excel_exporter.py   (styled Excel builder & matplotlib charts)
│   ├── api.py              (FastAPI routers, uploading, and file delivery)
│   └── main.py             (database seeder & server runner)
├── requirements.txt
└── README.md
```

---

## ⚙️ How to Setup and Run

### 1. Install Dependencies
Make sure you have Python installed, then install project requirements:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application Server
Run the main startup script:
```bash
python src/main.py
```
This initializes the database (`expenses.db`), seeds mock data if empty, and starts the FastAPI server.

### 3. Open the UI Dashboard
Open your web browser and navigate to:
```
http://localhost:8001
```
*(Note: Since Project 1 runs on port 8000, the Expense Tracker is configured to run on port 8001 to avoid conflicts.)*

---

## ⚡ REST API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/expenses` | Returns all expense rows sorted by date descending. |
| `POST` | `/api/expenses` | Inserts a new expense row. |
| `PUT` | `/api/expenses/{id}` | Updates an existing expense row. |
| `DELETE` | `/api/expenses/{id}` | Deletes an expense row by ID. |
| `GET` | `/api/expenses/summary` | Calculates core KPIs, categories breakdown, and daily totals. |
| `POST` | `/api/expenses/reset-mock` | Clears the database and seeds 30 new transaction rows. |
| `POST` | `/api/expenses/upload-csv` | Accepts raw CSV file, normalizes header mappings, and bulk inserts them. |
| `GET` | `/api/expenses/export-excel` | Triggers styled Excel generation and initiates a file download. |
| `GET` | `/api/expenses/download-sample-csv` | Serves an expense CSV import template file. |
