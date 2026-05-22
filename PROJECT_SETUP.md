# Bluestock Project Setup Guide

## ✅ What's Been Built So Far

### Stream B — Data Engineering Foundation ✓
- [x] **Docker Compose** setup with PostgreSQL 15 + Redis
- [x] **Star Schema DDL** (init.sql) with all dimensions and facts
- [x] **ETL Pipeline** (3 scripts):
  - `01_extract_from_mysql.py` — Parse SQL dump to CSVs
  - `02_clean_and_transform.py` — Standardize data, compute metrics
  - `03_load_to_warehouse.py` — Load to PostgreSQL with upsert
- [x] **Python environment** ready (requirements.txt)
- [x] **Sector mapping** for all 100 Nifty companies

### Stream C — Django API ✓
- [x] **Django project scaffold** (DRF + drf-spectacular)
- [x] **Models** (read-only mapping to warehouse)
- [x] **Serializers** (company detail, financials, health scores)
- [x] **ViewSets** (companies, sectors, health analytics)
- [x] **OpenAPI/Swagger** documentation ready
- [x] **API endpoints**:
  - `GET /api/companies/` — List all companies
  - `GET /api/companies/{symbol}/` — Company details
  - `GET /api/companies/{symbol}/health_score/` — Latest health
  - `GET /api/companies/{symbol}/financials/` — Financial history
  - `GET /api/sectors/summary/` — Sector aggregations

### Stream A — Power BI (TODO)
- [ ] **7 PBIX files** (templates created, waiting for data to populate)
- [ ] Power Query transformations
- [ ] DAX measures and KPIs
- [ ] Dashboard pages and visuals

---

## 🚀 Next Steps: Getting Started

### 1. Download Your Data
```bash
# Go to: https://drive.google.com/drive/folders/1qpx7VTfTo46GMDQ_dR3ctYK2G6zKYE8-
# Download the SQL dump (likely scriptticker.sql)
# Save to project root: /vercel/share/v0-project/scriptticker.sql
```

### 2. Install Python Dependencies
```bash
cd /vercel/share/v0-project
pip install -r requirements.txt
```

### 3. Start Docker Containers
```bash
docker-compose up -d

# Verify PostgreSQL is running
docker-compose logs postgres
# Should see: "database system is ready to accept connections"
```

### 4. Run ETL Pipeline
```bash
# Step 1: Extract from SQL dump
python etl/01_extract_from_mysql.py
# Output: data/raw/ folder with 7 CSVs

# Step 2: Clean and transform
python etl/02_clean_and_transform.py
# Output: data/clean/ folder with standardized CSVs

# Step 3: Load to PostgreSQL
python etl/03_load_to_warehouse.py
# Output: Populated warehouse tables
```

### 5. Verify Warehouse (Optional)
```bash
# Connect to PostgreSQL
psql -h localhost -U bluestock_user -d bluestock_dw

# Check row counts
SELECT 
  'dim_company' as table_name, COUNT(*) as rows FROM dim_company
UNION ALL
SELECT 'dim_year', COUNT(*) FROM dim_year
UNION ALL
SELECT 'fact_profit_loss', COUNT(*) FROM fact_profit_loss
UNION ALL
SELECT 'fact_balance_sheet', COUNT(*) FROM fact_balance_sheet
UNION ALL
SELECT 'fact_cash_flow', COUNT(*) FROM fact_cash_flow;
```

### 6. Start Django API
```bash
cd django_api
python manage.py runserver 0.0.0.0:8000
```

### 7. Test API
Open in browser:
```
http://localhost:8000/api/docs/
```

Click "Try it out" on any endpoint to test.

---

## 📁 Project Structure

```
bluestock/
├── etl/
│   ├── 01_extract_from_mysql.py
│   ├── 02_clean_and_transform.py
│   └── 03_load_to_warehouse.py
│
├── data/
│   ├── raw/          (CSVs from SQL dump)
│   └── clean/        (Standardized CSVs)
│
├── django_api/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   └── api/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── powerbi/          (7 PBIX files, empty)
│   ├── 01_executive_overview.pbix
│   ├── 02_company_deep_dive.pbix
│   ├── 03_sector_comparison.pbix
│   ├── 04_health_scorecard.pbix
│   ├── 05_growth_analytics.pbix
│   ├── 06_debt_leverage.pbix
│   └── 07_dividend_returns.pbix
│
├── notebooks/        (Jupyter notebooks for EDA)
│
├── docker-compose.yml
├── init.sql          (Star schema DDL)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── PROJECT_SETUP.md
```

---

## 🔧 Configuration

### Environment Variables (.env)
Copy from `.env.example`:
```bash
cp .env.example .env
```

Edit as needed:
```
DATABASE_URL=postgresql://bluestock_user:bluestock_pass@localhost:5432/bluestock_dw
REDIS_URL=redis://localhost:6379/0
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
```

---

## 📊 Data Model Summary

### Dimensions
- `dim_company` — 100 companies (symbol, name, sector, logos, URLs)
- `dim_year` — Standardized years (Mar 2024, TTM, etc.)
- `dim_sector` — 15 sectors (IT, Banking, Energy, etc.)
- `dim_health_label` — Score ranges (EXCELLENT, GOOD, AVERAGE, WEAK, POOR)

### Facts
- `fact_profit_loss` — P&L by company per year
- `fact_balance_sheet` — Balance sheet by company per year
- `fact_cash_flow` — Cash flow by company per year
- `fact_analysis` — Growth metrics (10Y/5Y/3Y/TTM CAGR)
- `fact_ml_scores` — ML health scores (updated weekly)
- `fact_pros_cons` — AI-generated insights

---

## 🎯 Work by Stream

### Stream A (40% time) — Power BI Dashboards
**Status:** Ready for data  
**Next:** 
1. Connect Power BI to PostgreSQL
2. Import all dim_* and fact_* tables
3. Set up relationships (see README.md Section 4.2)
4. Build 7 dashboards from spec

### Stream B (35% time) — Data Engineering
**Status:** Infrastructure complete  
**Next:**
1. ✅ ETL pipeline built
2. TODO: ML scoring module (Python + Celery)
3. TODO: Weekly scheduled updates
4. TODO: Data quality monitoring

### Stream C (25% time) — Django API
**Status:** Scaffolded and ready  
**Next:**
1. ✅ Core API endpoints built
2. TODO: Channel partner authentication
3. TODO: Rate limiting & API keys
4. TODO: Deploy to Vercel/AWS/Railway

---

## 🐛 Troubleshooting

### PostgreSQL won't start
```bash
docker-compose down
docker-compose up -d
docker-compose logs postgres
```

### ETL script fails
```bash
# Check if SQL dump exists
ls -la *.sql

# Verify data format
head -n 50 scriptticker.sql

# Check Python version
python --version  # Should be 3.11+
```

### API connection error
```bash
# Verify PostgreSQL is running
psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT 1"

# Check Django settings
python django_api/manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
```

---

## 📋 Todos Tracker

Track progress using TodoManager:
1. **Stream B — ETL Pipeline & PostgreSQL Warehouse Setup** (In Progress)
2. **Stream B — Data Extraction, Cleaning, ML Scoring Scripts** (Next)
3. **Stream A — Power BI Data Model & 7 Dashboards** (Queued)
4. **Stream C — Django Web App & REST API** (Queued)
5. **Stream C — API Documentation & Channel Partner Features** (Queued)
6. **Integration & Testing** (Queued)

---

## 💡 Key Design Decisions

1. **Star Schema** — Optimized for Power BI and analytics queries
2. **Python ETL** — Flexible, easy to debug, no proprietary tools
3. **PostgreSQL** — Open source, free, scales to billions of rows
4. **Django REST** — Mature, well-documented, production-ready
5. **Read-only Models** — API maps to warehouse (no write logic)
6. **Upsert Logic** — ETL is idempotent (can run multiple times)

---

## 📞 Need Help?

1. Check the **README.md** for full documentation
2. Review **init.sql** to understand the schema
3. Look at ETL scripts for transformation logic
4. Test API at http://localhost:8000/api/docs/

Now, **download your SQL dump and run the ETL!**
