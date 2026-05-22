# Bluestock: Nifty 100 Financial Intelligence System

A comprehensive financial analytics platform for India's top 100 publicly listed companies (Nifty 100).

**Three parallel streams:**
- **Stream A** — 7 Production-grade Power BI dashboards  
- **Stream B** — ETL pipelines, PostgreSQL warehouse, ML scoring  
- **Stream C** — Django web app + REST API for channel partners

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15
- Git

### Setup

1. **Clone and install dependencies**
   ```bash
   git clone <repo>
   cd bluestock
   cp .env.example .env
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Place your SQL dump**
   - Download the SQL dump from: https://drive.google.com/drive/folders/1qpx7VTfTo46GMDQ_dR3ctYK2G6zKYE8-
   - Save it as `scriptticker.sql` in the project root

4. **Run ETL Pipeline**
   ```bash
   # Extract from SQL dump
   python etl/01_extract_from_mysql.py
   
   # Clean and transform
   python etl/02_clean_and_transform.py
   
   # Load into warehouse
   python etl/03_load_to_warehouse.py
   ```

5. **Verify warehouse**
   ```bash
   psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT COUNT(*) FROM dim_company;"
   ```

---

## Project Structure

```
bluestock/
├── etl/                          # ETL pipeline scripts
│   ├── 01_extract_from_mysql.py  # Parse SQL dump
│   ├── 02_clean_and_transform.py # Data cleaning
│   └── 03_load_to_warehouse.py   # Load to PostgreSQL
├── data/
│   ├── raw/                      # Extracted CSVs
│   ├── clean/                    # Cleaned CSVs
│   └── sector_mapping.csv        # Sector classification
├── powerbi/                      # Power BI PBIX files
│   ├── 01_executive_overview.pbix
│   ├── 02_company_deep_dive.pbix
│   ├── 03_sector_comparison.pbix
│   ├── 04_health_scorecard.pbix
│   ├── 05_growth_analytics.pbix
│   ├── 06_debt_leverage.pbix
│   └── 07_dividend_returns.pbix
├── django_api/                   # Django REST API
│   ├── manage.py
│   ├── settings.py
│   └── api/
├── notebooks/                    # Jupyter notebooks for EDA
├── docker-compose.yml            # PostgreSQL + Redis stack
├── init.sql                      # Star schema DDL
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

---

## Data Model

### Dimension Tables
- **dim_company** — Company master (100 companies, sectors, logos, links)
- **dim_year** — Year standardization (handles Mar 2024, TTM, etc.)
- **dim_sector** — Sector classification (IT, Banking, Energy, etc.)
- **dim_health_label** — Health score labels (EXCELLENT, GOOD, AVERAGE, WEAK, POOR)

### Fact Tables
- **fact_profit_loss** — Annual P&L (12 years per company)
- **fact_balance_sheet** — Annual balance sheet
- **fact_cash_flow** — Annual cash flow
- **fact_analysis** — Growth metrics (10Y/5Y/3Y/TTM)
- **fact_ml_scores** — ML-computed health scores (updated weekly)
- **fact_pros_cons** — AI-generated pros/cons insights

---

## Power BI Dashboards

Seven production-grade dashboards for different audiences:

| Dashboard | Audience | Focus |
|-----------|----------|-------|
| 01 Executive Overview | Fund managers, CXOs | Nifty 100 snapshot, sector performance |
| 02 Company Deep Dive | Individual investors, analysts | Single company: financials, health, growth |
| 03 Sector Comparison | Sector analysts | Cross-sector benchmarking |
| 04 Health Scorecard | Risk managers, portfolio teams | Company scoring, peer comparison |
| 05 Growth Analytics | Growth investors | Revenue/profit growth, margin evolution |
| 06 Debt & Leverage | Credit analysts | D/E trends, interest coverage, risk |
| 07 Dividend Returns | Income investors | Dividend history, shareholder value |

**To use in Power BI:**
1. Open Power BI Desktop
2. Get Data → PostgreSQL
3. Server: `localhost:5432`, Database: `bluestock_dw`
4. Import all `dim_*` and `fact_*` tables
5. Open the PBIX file from `powerbi/` folder

---

## Django API

### Setup
```bash
cd django_api
python manage.py migrate
python manage.py runserver
```

### Available Endpoints
- `GET /api/companies/` — List all companies with health scores
- `GET /api/companies/{symbol}/` — Company deep dive (financials, health, peers)
- `GET /api/sectors/` — Sector-level aggregations
- `GET /api/analysis/{symbol}/?period=3Y` — Growth metrics (10Y/5Y/3Y/TTM)

### Interactive API Docs
Visit: http://localhost:8000/api/docs/ (Swagger/OpenAPI)

---

## ML Scoring

The ML health score is computed weekly on 8 dimensions:
1. **Profitability** — OPM%, net margin, ROE
2. **Growth** — 3Y sales/profit CAGR
3. **Leverage** — Debt-to-equity, interest coverage
4. **Cash Flow** — Operating cash, conversion ratio
5. **Dividend** — Payout consistency, growth
6. **Trend** — YoY acceleration/deceleration
7. **Returns** — ROE, ROCE, asset turnover
8. **Balance** — Sector-relative scoring

Score: 0–100 → Label (EXCELLENT/GOOD/AVERAGE/WEAK/POOR)

---

## ETL Pipeline & Scheduling

### Manual Run
```bash
python etl/01_extract_from_mysql.py
python etl/02_clean_and_transform.py
python etl/03_load_to_warehouse.py
```

### Scheduled (Celery + Redis)
```bash
# Start worker
celery -A django_api worker -l info

# Periodic tasks run via celery-beat
# Default: ETL runs every Sunday at 2 AM IST
```

---

## Common Commands

```bash
# Check PostgreSQL
psql -h localhost -U bluestock_user -d bluestock_dw

# View data counts
SELECT table_name, 
       (SELECT COUNT(*) FROM <table>) as row_count 
FROM information_schema.tables 
WHERE table_schema='public';

# Restart Docker containers
docker-compose down
docker-compose up -d

# View logs
docker-compose logs -f postgres
```

---

## Next Steps

1. **Download your data** — Get the SQL dump from Google Drive
2. **Run ETL** — Follow the setup steps above
3. **Connect Power BI** — Open dashboards and explore
4. **Deploy Django** — Host the web app and API (Vercel, Railway, AWS)
5. **Set up scheduler** — Configure Celery for automated updates

---

## Support

For issues, questions, or feature requests:
- Check the ETL logs in `data/logs/`
- Review PostgreSQL error logs: `docker-compose logs postgres`
- Test Power BI connectivity: `Get Data → PostgreSQL Diagnostics`

---

**Built with:** Python 3.11 | PostgreSQL 15 | Power BI | Django 4.2 | Celery | Redis
