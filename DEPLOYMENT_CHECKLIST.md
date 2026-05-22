# Bluestock Deployment Checklist

Quick reference for getting Bluestock live.

## Phase 1: Local Development Setup (1-2 hours)

### Prerequisites
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Docker & Docker Compose installed (`docker --version`)
- [ ] Git installed (`git --version`)
- [ ] PostgreSQL client installed (`psql --version`)

### Environment Setup
- [ ] Clone repository
- [ ] Copy `.env.example` → `.env`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip install -r requirements.txt`

### Data Preparation
- [ ] Download SQL dump from Google Drive
- [ ] Save as `scriptticker.sql` in project root
- [ ] Verify file exists: `ls -la scriptticker.sql`
- [ ] Check file size is reasonable (>10MB)

### Docker Services
- [ ] Start PostgreSQL + Redis: `docker-compose up -d`
- [ ] Verify PostgreSQL: `docker-compose logs postgres` (should see "ready to accept")
- [ ] Verify Redis: `docker-compose logs redis`
- [ ] Test connection: `psql -h localhost -U bluestock_user -d bluestock_dw -c "SELECT 1"`

## Phase 2: Data Pipeline Execution (1-2 hours)

### ETL Pipeline
- [ ] **Extract:** `python etl/01_extract_from_mysql.py`
  - Check output: `ls data/raw/` (should have 7 CSVs)
  - Verify row counts printed match expected data
  
- [ ] **Transform:** `python etl/02_clean_and_transform.py`
  - Check output: `ls data/clean/` (should have 7 CSVs + sector_mapping.csv)
  - Verify sector mapping: 100 companies classified
  
- [ ] **Load:** `python etl/03_load_to_warehouse.py`
  - Should print row counts for each table
  - Verify no constraint violations
  - Data quality checks should pass

### Warehouse Validation
```bash
# Run these manually to confirm data loaded
psql -h localhost -U bluestock_user -d bluestock_dw -c "
  SELECT table_name, 
         (SELECT COUNT(*) FROM information_schema.tables t 
          WHERE t.table_name = table_name) as exists
  FROM (
    VALUES 
      ('dim_company'), ('dim_sector'), ('dim_year'),
      ('fact_profit_loss'), ('fact_balance_sheet'), ('fact_cash_flow'),
      ('fact_analysis')
  ) t(table_name);
"
```

- [ ] dim_company: ~100 rows
- [ ] dim_year: 12-16 rows
- [ ] dim_sector: 15 rows
- [ ] fact_profit_loss: ~1.2M rows
- [ ] fact_balance_sheet: ~1.2M rows
- [ ] fact_cash_flow: ~1.2M rows
- [ ] fact_analysis: ~400 rows

### ML Scoring (Optional, can skip first run)
- [ ] Run: `python etl/ml_scoring.py`
- [ ] Verify: `psql -c "SELECT COUNT(*) FROM fact_ml_scores;"`
- [ ] Check report output (top/bottom companies printed)

## Phase 3: Django API Setup (30-45 minutes)

### Django Configuration
- [ ] Navigate: `cd django_api`
- [ ] Run: `python manage.py shell`
  - In shell: `from api.models import DimCompany; print(DimCompany.objects.count())`
  - Should return: `100`
  - Exit shell: `exit()`

### API Server
- [ ] Start: `python manage.py runserver 0.0.0.0:8000`
- [ ] Test in browser: `http://localhost:8000/api/docs/`
  - Should see Swagger UI
  - All endpoints listed

### API Endpoint Verification
- [ ] `GET /api/companies/` → Returns list of companies
- [ ] `GET /api/companies/TCS/` → Returns TCS details
- [ ] `GET /api/sectors/` → Returns sector list
- [ ] `GET /api/companies/TCS/health_score/` → Returns health data (if ML ran)

## Phase 4: Power BI Connection (1-2 hours)

### Power BI Desktop
- [ ] Open Power BI Desktop
- [ ] Get Data → PostgreSQL Database
  - Server: `localhost`
  - Database: `bluestock_dw`
- [ ] Import all tables:
  - [ ] dim_company
  - [ ] dim_year
  - [ ] dim_sector
  - [ ] dim_health_label
  - [ ] fact_profit_loss
  - [ ] fact_balance_sheet
  - [ ] fact_cash_flow
  - [ ] fact_analysis
  - [ ] fact_ml_scores (if available)

### Data Model
- [ ] Model view: Right-click → Manage relationships
- [ ] Create relationships (8 total):
  - [ ] fact_profit_loss[symbol] → dim_company[symbol] (M:1)
  - [ ] fact_profit_loss[year_id] → dim_year[year_id] (M:1)
  - [ ] fact_balance_sheet[symbol] → dim_company[symbol] (M:1)
  - [ ] fact_balance_sheet[year_id] → dim_year[year_id] (M:1)
  - [ ] fact_cash_flow[symbol] → dim_company[symbol] (M:1)
  - [ ] fact_cash_flow[year_id] → dim_year[year_id] (M:1)
  - [ ] fact_analysis[symbol] → dim_company[symbol] (M:1)
  - [ ] fact_ml_scores[symbol] → dim_company[symbol] (M:1)
  - [ ] dim_company[sector_id] → dim_sector[sector_id] (M:1)

### Dashboard Building
- [ ] Open template: `powerbi/01_executive_overview.pbix`
- [ ] Verify data loaded and relationships work
- [ ] Test a simple visual (card, chart)
- [ ] Repeat for other dashboards as needed

## Phase 5: Scheduling & Automation (30 minutes)

### Celery Setup (Optional for initial launch)
- [ ] Start Celery worker: `celery -A config worker -l info` (in separate terminal, from django_api/)
- [ ] Start Celery beat: `celery -A config beat -l info` (in another terminal)
- [ ] Verify tasks registered: `celery -A config inspect registered_tasks`

### Manual Scheduling (Simpler, for MVP)
- [ ] OS cron job (Linux/Mac) or Task Scheduler (Windows)
- [ ] Weekly trigger: `python /path/to/bluestock/etl/ml_scoring.py`
- [ ] Keep error logs for monitoring

## Phase 6: Production Deployment (2-4 hours, depends on platform)

### Option A: Vercel (Recommended for API)
- [ ] Create Vercel account
- [ ] Connect GitHub repo
- [ ] Add environment variables:
  - [ ] DATABASE_URL (production PostgreSQL)
  - [ ] REDIS_URL (if using Celery)
  - [ ] SECRET_KEY
- [ ] Deploy: `git push origin main`
- [ ] Verify: `https://your-project.vercel.app/api/docs/`

### Option B: Railway (Recommended for full stack)
- [ ] Create Railway account
- [ ] Connect GitHub repo
- [ ] Create services:
  - [ ] Django app
  - [ ] PostgreSQL database (or link external)
  - [ ] Redis (optional, for Celery)
- [ ] Set environment variables
- [ ] Deploy: `git push` (auto-deploys)
- [ ] Verify: `https://your-project.railway.app/api/docs/`

### Option C: AWS (For enterprise)
- [ ] RDS: Create PostgreSQL instance
- [ ] EC2: Launch Ubuntu instance
- [ ] Clone repo, install dependencies
- [ ] Run ETL and Django app
- [ ] Setup auto-scaling, backups, monitoring

### Database Migration
- [ ] Backup local database: `pg_dump bluestock_dw > backup.sql`
- [ ] Restore to production: `psql -h prod-host -U user -d bluestock_dw < backup.sql`
- [ ] Update `.env` with production DATABASE_URL
- [ ] Test connection: `python manage.py shell`

### Power BI Cloud Connection
- [ ] Power BI Service (app.powerbi.com)
- [ ] Publish PBIX files from Desktop
- [ ] Setup gateway for on-premises PostgreSQL (if needed)
- [ ] Configure scheduled refresh (daily or weekly)
- [ ] Share dashboards with stakeholders

## Phase 7: Post-Launch Validation (1 hour)

### Functional Tests
- [ ] API responds to all endpoints
- [ ] Power BI dashboards load and refresh data
- [ ] Django admin works (if needed)
- [ ] Health scores update weekly

### Performance Tests
- [ ] Dashboard load time < 5 seconds
- [ ] API response time < 200ms
- [ ] Database queries complete in < 1 second

### Data Validation
- [ ] All 100 companies present in dim_company
- [ ] All years present in dim_year
- [ ] No orphaned foreign keys
- [ ] Health scores in valid range (0-100)

### Monitoring Setup
- [ ] Application logs configured
- [ ] Database query monitoring enabled
- [ ] Error alerting setup (email or Slack)
- [ ] Weekly backup verification

## Phase 8: Documentation & Handoff

- [ ] README.md reviewed and complete
- [ ] API documentation live at `/api/docs/`
- [ ] Dashboard business glossary created
- [ ] Runbook for weekly updates written
- [ ] Team trained on dashboard usage
- [ ] Stakeholder access granted

## Rollback Plan

If production fails:

1. **API Down:**
   - Rollback last commit: `git revert HEAD`
   - Check logs: `vercel logs` or Railway logs
   - Verify database connectivity

2. **Data Corrupted:**
   - Restore from backup: `psql < backup.sql`
   - Rerun ETL pipeline
   - Verify health scores

3. **Dashboard Broken:**
   - Redownload PBIX files
   - Recreate relationships in Power BI
   - Republish to Power BI Service

## Support Contacts

- **Database Issues:** PostgreSQL logs, check `docker-compose logs postgres`
- **ETL Failures:** Review `data/logs/` or script output
- **API Errors:** Check `/api/docs/` Swagger for request/response format
- **Power BI Questions:** Power BI docs → power-bi.microsoft.com

---

## Success Criteria

Launch is successful when:

✅ All 100 companies loaded into warehouse  
✅ ETL pipeline runs without errors  
✅ Django API accessible and returns data  
✅ 7 Power BI dashboards displaying updated data  
✅ Health scores computed and visible  
✅ Team can query data independently  
✅ Scheduled updates running weekly  
✅ Monitoring and alerting configured  

**Ready to launch! 🚀**
