# Bluestock Quick Start (TL;DR)

## 1. Prepare (10 mins)

```bash
# Clone
git clone <repo>
cd bluestock

# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Copy config
cp .env.example .env

# Start services
docker-compose up -d
```

## 2. Load Data (20 mins)

```bash
# Download: https://drive.google.com/drive/folders/1qpx7VTfTo46GMDQ_dR3ctYK2G6zKYE8-
# Save as: scriptticker.sql

# Run ETL
python etl/01_extract_from_mysql.py     # → data/raw/
python etl/02_clean_and_transform.py    # → data/clean/
python etl/03_load_to_warehouse.py      # → PostgreSQL

# Score companies
python etl/ml_scoring.py                # → health scores
```

## 3. Verify (5 mins)

```bash
# Check warehouse
psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT COUNT(*) FROM dim_company;"
# Should return: 100

# Check scores
psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT COUNT(*) FROM fact_ml_scores;"
# Should return: ~100
```

## 4. API (5 mins)

```bash
cd django_api
python manage.py runserver

# Test: http://localhost:8000/api/docs/
# Try: GET /api/companies/
```

## 5. Power BI (30 mins)

```
Power BI Desktop:
→ Get Data
→ PostgreSQL
→ Server: localhost
→ Database: bluestock_dw
→ Import all dim_* and fact_* tables
→ Model → Create relationships
→ Open: powerbi/02_company_deep_dive.pbix
```

---

## Commands Cheat Sheet

```bash
# Docker
docker-compose up -d                # Start services
docker-compose down                 # Stop services
docker-compose logs postgres        # View logs

# PostgreSQL
psql -h localhost -U bluestock_user -d bluestock_dw
psql> \dt                           # List tables
psql> SELECT COUNT(*) FROM dim_company;  # Company count
psql> \q                            # Exit

# Python
python etl/01_extract_from_mysql.py # Extract
python etl/02_clean_and_transform.py # Transform
python etl/03_load_to_warehouse.py   # Load
python etl/ml_scoring.py            # Score

# Django
cd django_api
python manage.py runserver          # Start API
python manage.py shell              # Interactive shell
# In shell:
from api.models import DimCompany
print(DimCompany.objects.count())   # Should be 100

# Celery (optional, for scheduling)
celery -A config worker -l info     # Worker
celery -A config beat -l info       # Scheduler
```

---

## Key Files

| File | Purpose |
|------|---------|
| `etl/01_extract_from_mysql.py` | Parse SQL dump |
| `etl/02_clean_and_transform.py` | Standardize data |
| `etl/03_load_to_warehouse.py` | Load to DB |
| `etl/ml_scoring.py` | Health scores |
| `django_api/` | REST API |
| `powerbi/` | 7 dashboards |
| `init.sql` | Database schema |
| `.env.example` | Config template |

---

## Common Issues

### "Can't find scriptticker.sql"
```bash
# Make sure file is in project root
ls -la scriptticker.sql
```

### "Database connection failed"
```bash
# Start Docker
docker-compose up -d

# Wait 10 seconds, then test
psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT 1;"
```

### "No module named pandas"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "Port 5432 already in use"
```bash
# Stop existing PostgreSQL or change port in docker-compose.yml
docker ps  # See what's running
```

---

## Success Indicators

- [x] Docker running: `docker ps`
- [x] PostgreSQL responds: `psql` connection works
- [x] ETL completes: No error messages
- [x] Warehouse populated: 100 companies loaded
- [x] Health scores: ~100 records in fact_ml_scores
- [x] API responds: `http://localhost:8000/api/docs/` loads
- [x] Power BI connects: PostgreSQL data visible

---

## Full Documentation

- **Setup details** → `PROJECT_SETUP.md`
- **Architecture** → `IMPLEMENTATION.md`
- **Launch checklist** → `DEPLOYMENT_CHECKLIST.md`
- **Project overview** → `SUMMARY.md`
- **README** → `README.md`

---

## Support

1. Check error messages (usually tell you what's wrong)
2. Read `PROJECT_SETUP.md` troubleshooting section
3. Verify PostgreSQL is running: `docker-compose logs postgres`
4. Check if data loaded: `psql` and run `SELECT COUNT(*) FROM dim_company;`

---

## Timeline

- **Extract (5 mins):** `python etl/01_extract_from_mysql.py`
- **Transform (3 mins):** `python etl/02_clean_and_transform.py`
- **Load (5 mins):** `python etl/03_load_to_warehouse.py`
- **Score (2 mins):** `python etl/ml_scoring.py`
- **API ready (immediate):** `python manage.py runserver`
- **Power BI (30 mins):** Connect and build dashboards

**Total: ~1 hour to full launch**

---

## Next Steps

1. Download SQL dump
2. Run ETL (3 scripts)
3. Start API
4. Connect Power BI
5. Done!

🚀 **You're live!**
