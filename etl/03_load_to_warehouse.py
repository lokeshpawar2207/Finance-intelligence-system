"""
ETL Script 3: Load cleaned data into PostgreSQL warehouse
Purpose: Load all cleaned CSVs into star schema tables with upsert logic
Output: Populated PostgreSQL database
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://bluestock_user:bluestock_pass@localhost:5432/bluestock_dw'
)

CLEAN_DATA_DIR = Path("data/clean")

class WarehouseLoader:
    """Load cleaned data into PostgreSQL warehouse"""
    
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✓ Database connection successful")
                return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def load_dim_company(self):
        """Load dimension_company from cleaned companies CSV"""
        print("Loading dim_company...")
        
        file_path = CLEAN_DATA_DIR / 'companies.csv'
        if not file_path.exists():
            print(f"  SKIP: {file_path} not found")
            return
        
        df = pd.read_csv(file_path)
        
        # Select required columns
        cols_needed = [
            'symbol', 'company_name', 'sector', 'sub_sector',
            'company_logo', 'website', 'nse_url', 'bse_url',
            'face_value', 'book_value', 'about_company'
        ]
        
        df_clean = df[[col for col in cols_needed if col in df.columns]].copy()
        df_clean.columns = [
            'symbol', 'company_name', 'sector', 'sub_sector',
            'company_logo', 'website', 'nse_url', 'bse_url',
            'face_value', 'book_value', 'about_company'
        ]
        
        # First, get sector_id from dim_sector
        with self.engine.connect() as conn:
            sector_query = "SELECT sector_id, sector_name FROM dim_sector"
            sectors = pd.read_sql(sector_query, conn)
            sector_map = dict(zip(sectors['sector_name'], sectors['sector_id']))
        
        df_clean['sector_id'] = df_clean['sector'].map(sector_map)
        
        # Select final columns for insert
        insert_cols = [
            'symbol', 'company_name', 'sector_id', 'sub_sector',
            'company_logo', 'website', 'nse_url', 'bse_url',
            'face_value', 'book_value', 'about_company'
        ]
        
        df_insert = df_clean[insert_cols].fillna('')
        
        # Upsert using ON CONFLICT DO UPDATE
        with self.engine.connect() as conn:
            for _, row in df_insert.iterrows():
                upsert_sql = text("""
                    INSERT INTO dim_company 
                    (symbol, company_name, sector_id, sub_sector, company_logo, 
                     website, nse_url, bse_url, face_value, book_value, about_company)
                    VALUES 
                    (:symbol, :company_name, :sector_id, :sub_sector, :company_logo,
                     :website, :nse_url, :bse_url, :face_value, :book_value, :about_company)
                    ON CONFLICT (symbol) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        sector_id = EXCLUDED.sector_id,
                        sub_sector = EXCLUDED.sub_sector,
                        company_logo = EXCLUDED.company_logo,
                        website = EXCLUDED.website,
                        nse_url = EXCLUDED.nse_url,
                        bse_url = EXCLUDED.bse_url,
                        face_value = EXCLUDED.face_value,
                        book_value = EXCLUDED.book_value,
                        about_company = EXCLUDED.about_company,
                        updated_at = CURRENT_TIMESTAMP
                """)
                conn.execute(upsert_sql, row.to_dict())
            conn.commit()
        
        print(f"  ✓ Loaded {len(df_insert)} companies")
    
    def load_dim_year(self):
        """Load dim_year from cleaned data"""
        print("Loading dim_year...")
        
        years_set = set()
        
        # Collect all years from fact tables
        for table in ['balancesheet', 'profitandloss', 'cashflow']:
            file_path = CLEAN_DATA_DIR / f'{table}.csv'
            if file_path.exists():
                df = pd.read_csv(file_path)
                if 'year_label' in df.columns:
                    years_set.update(df['year_label'].dropna().unique())
        
        years_list = []
        for year_label in sorted(years_set):
            row = {
                'year_label': year_label,
                'fiscal_year': None,
                'quarter': None,
                'is_ttm': False,
                'is_half_year': False,
                'sort_order': 0
            }
            
            if year_label == 'TTM':
                row['is_ttm'] = True
                row['sort_order'] = 99999
            else:
                # Extract year for sort order
                import re
                match = re.search(r'(\d{4})', year_label)
                if match:
                    year = int(match.group(1))
                    row['fiscal_year'] = year
                    row['sort_order'] = 9999 - year
            
            years_list.append(row)
        
        years_df = pd.DataFrame(years_list)
        
        with self.engine.connect() as conn:
            for _, row in years_df.iterrows():
                upsert_sql = text("""
                    INSERT INTO dim_year (year_label, fiscal_year, quarter, is_ttm, is_half_year, sort_order)
                    VALUES (:year_label, :fiscal_year, :quarter, :is_ttm, :is_half_year, :sort_order)
                    ON CONFLICT (year_label) DO UPDATE SET
                        fiscal_year = EXCLUDED.fiscal_year,
                        quarter = EXCLUDED.quarter,
                        is_ttm = EXCLUDED.is_ttm,
                        is_half_year = EXCLUDED.is_half_year,
                        sort_order = EXCLUDED.sort_order
                """)
                conn.execute(upsert_sql, row.to_dict())
            conn.commit()
        
        print(f"  ✓ Loaded {len(years_df)} year labels")
    
    def load_fact_profit_loss(self):
        """Load fact_profit_loss"""
        print("Loading fact_profit_loss...")
        
        file_path = CLEAN_DATA_DIR / 'profitandloss.csv'
        if not file_path.exists():
            print(f"  SKIP: {file_path} not found")
            return
        
        df = pd.read_csv(file_path)
        
        # Get year_id mapping
        with self.engine.connect() as conn:
            year_query = "SELECT year_id, year_label FROM dim_year"
            years = pd.read_sql(year_query, conn)
            year_map = dict(zip(years['year_label'], years['year_id']))
        
        required_cols = [
            'symbol', 'year_label', 'sales', 'expenses', 'operating_profit', 'opm_pct',
            'other_income', 'interest', 'depreciation', 'profit_before_tax', 'tax_pct',
            'net_profit', 'eps', 'dividend_payout_pct', 'net_profit_margin_pct',
            'expense_ratio_pct', 'interest_coverage'
        ]
        
        df_insert = df[[col for col in required_cols if col in df.columns]].copy()
        df_insert['year_id'] = df_insert['year_label'].map(year_map)
        df_insert = df_insert.dropna(subset=['year_id'])
        df_insert['year_id'] = df_insert['year_id'].astype(int)
        
        with self.engine.connect() as conn:
            for _, row in df_insert.iterrows():
                upsert_sql = text("""
                    INSERT INTO fact_profit_loss 
                    (symbol, year_id, sales, expenses, operating_profit, opm_pct,
                     other_income, interest, depreciation, profit_before_tax, tax_pct,
                     net_profit, eps, dividend_payout_pct, net_profit_margin_pct,
                     expense_ratio_pct, interest_coverage)
                    VALUES 
                    (:symbol, :year_id, :sales, :expenses, :operating_profit, :opm_pct,
                     :other_income, :interest, :depreciation, :profit_before_tax, :tax_pct,
                     :net_profit, :eps, :dividend_payout_pct, :net_profit_margin_pct,
                     :expense_ratio_pct, :interest_coverage)
                    ON CONFLICT (symbol, year_id) DO UPDATE SET
                        sales = EXCLUDED.sales,
                        expenses = EXCLUDED.expenses,
                        operating_profit = EXCLUDED.operating_profit,
                        opm_pct = EXCLUDED.opm_pct,
                        other_income = EXCLUDED.other_income,
                        interest = EXCLUDED.interest,
                        depreciation = EXCLUDED.depreciation,
                        profit_before_tax = EXCLUDED.profit_before_tax,
                        tax_pct = EXCLUDED.tax_pct,
                        net_profit = EXCLUDED.net_profit,
                        eps = EXCLUDED.eps,
                        dividend_payout_pct = EXCLUDED.dividend_payout_pct,
                        net_profit_margin_pct = EXCLUDED.net_profit_margin_pct,
                        expense_ratio_pct = EXCLUDED.expense_ratio_pct,
                        interest_coverage = EXCLUDED.interest_coverage,
                        updated_at = CURRENT_TIMESTAMP
                """)
                conn.execute(upsert_sql, row.to_dict())
            conn.commit()
        
        print(f"  ✓ Loaded {len(df_insert)} profit & loss records")
    
    def load_fact_balance_sheet(self):
        """Load fact_balance_sheet"""
        print("Loading fact_balance_sheet...")
        
        file_path = CLEAN_DATA_DIR / 'balancesheet.csv'
        if not file_path.exists():
            print(f"  SKIP: {file_path} not found")
            return
        
        df = pd.read_csv(file_path)
        
        # Get year_id mapping
        with self.engine.connect() as conn:
            year_query = "SELECT year_id, year_label FROM dim_year"
            years = pd.read_sql(year_query, conn)
            year_map = dict(zip(years['year_label'], years['year_id']))
        
        required_cols = [
            'symbol', 'year_label', 'equity_capital', 'reserves', 'borrowings',
            'other_liabilities', 'total_liabilities', 'fixed_assets', 'cwip',
            'investments', 'other_assets', 'total_assets', 'debt_to_equity', 'equity_ratio'
        ]
        
        df_insert = df[[col for col in required_cols if col in df.columns]].copy()
        df_insert['year_id'] = df_insert['year_label'].map(year_map)
        df_insert = df_insert.dropna(subset=['year_id'])
        df_insert['year_id'] = df_insert['year_id'].astype(int)
        
        with self.engine.connect() as conn:
            for _, row in df_insert.iterrows():
                upsert_sql = text("""
                    INSERT INTO fact_balance_sheet 
                    (symbol, year_id, equity_capital, reserves, borrowings,
                     other_liabilities, total_liabilities, fixed_assets, cwip,
                     investments, other_assets, total_assets, debt_to_equity, equity_ratio)
                    VALUES 
                    (:symbol, :year_id, :equity_capital, :reserves, :borrowings,
                     :other_liabilities, :total_liabilities, :fixed_assets, :cwip,
                     :investments, :other_assets, :total_assets, :debt_to_equity, :equity_ratio)
                    ON CONFLICT (symbol, year_id) DO UPDATE SET
                        equity_capital = EXCLUDED.equity_capital,
                        reserves = EXCLUDED.reserves,
                        borrowings = EXCLUDED.borrowings,
                        other_liabilities = EXCLUDED.other_liabilities,
                        total_liabilities = EXCLUDED.total_liabilities,
                        fixed_assets = EXCLUDED.fixed_assets,
                        cwip = EXCLUDED.cwip,
                        investments = EXCLUDED.investments,
                        other_assets = EXCLUDED.other_assets,
                        total_assets = EXCLUDED.total_assets,
                        debt_to_equity = EXCLUDED.debt_to_equity,
                        equity_ratio = EXCLUDED.equity_ratio,
                        updated_at = CURRENT_TIMESTAMP
                """)
                conn.execute(upsert_sql, row.to_dict())
            conn.commit()
        
        print(f"  ✓ Loaded {len(df_insert)} balance sheet records")
    
    def load_fact_cash_flow(self):
        """Load fact_cash_flow"""
        print("Loading fact_cash_flow...")
        
        file_path = CLEAN_DATA_DIR / 'cashflow.csv'
        if not file_path.exists():
            print(f"  SKIP: {file_path} not found")
            return
        
        df = pd.read_csv(file_path)
        
        # Get year_id mapping
        with self.engine.connect() as conn:
            year_query = "SELECT year_id, year_label FROM dim_year"
            years = pd.read_sql(year_query, conn)
            year_map = dict(zip(years['year_label'], years['year_id']))
        
        required_cols = [
            'symbol', 'year_label', 'operating_activity', 'investing_activity',
            'financing_activity', 'net_cash_flow', 'free_cash_flow', 'cash_conversion_ratio'
        ]
        
        df_insert = df[[col for col in required_cols if col in df.columns]].copy()
        df_insert['year_id'] = df_insert['year_label'].map(year_map)
        df_insert = df_insert.dropna(subset=['year_id'])
        df_insert['year_id'] = df_insert['year_id'].astype(int)
        
        with self.engine.connect() as conn:
            for _, row in df_insert.iterrows():
                upsert_sql = text("""
                    INSERT INTO fact_cash_flow 
                    (symbol, year_id, operating_activity, investing_activity,
                     financing_activity, net_cash_flow, free_cash_flow, cash_conversion_ratio)
                    VALUES 
                    (:symbol, :year_id, :operating_activity, :investing_activity,
                     :financing_activity, :net_cash_flow, :free_cash_flow, :cash_conversion_ratio)
                    ON CONFLICT (symbol, year_id) DO UPDATE SET
                        operating_activity = EXCLUDED.operating_activity,
                        investing_activity = EXCLUDED.investing_activity,
                        financing_activity = EXCLUDED.financing_activity,
                        net_cash_flow = EXCLUDED.net_cash_flow,
                        free_cash_flow = EXCLUDED.free_cash_flow,
                        cash_conversion_ratio = EXCLUDED.cash_conversion_ratio,
                        updated_at = CURRENT_TIMESTAMP
                """)
                conn.execute(upsert_sql, row.to_dict())
            conn.commit()
        
        print(f"  ✓ Loaded {len(df_insert)} cash flow records")
    
    def load_all(self):
        """Execute all loading steps"""
        print("Starting warehouse load...\n")
        
        if not self.test_connection():
            return
        
        print()
        self.load_dim_company()
        print()
        self.load_dim_year()
        print()
        self.load_fact_profit_loss()
        print()
        self.load_fact_balance_sheet()
        print()
        self.load_fact_cash_flow()
        
        self.run_data_quality_checks()
    
    def run_data_quality_checks(self):
        """Run post-load data quality checks"""
        print("\n" + "="*60)
        print("DATA QUALITY CHECKS")
        print("="*60)
        
        checks = {
            'dim_company': 'SELECT COUNT(*) as cnt FROM dim_company',
            'dim_year': 'SELECT COUNT(*) as cnt FROM dim_year',
            'fact_profit_loss': 'SELECT COUNT(*) as cnt FROM fact_profit_loss',
            'fact_balance_sheet': 'SELECT COUNT(*) as cnt FROM fact_balance_sheet',
            'fact_cash_flow': 'SELECT COUNT(*) as cnt FROM fact_cash_flow',
        }
        
        with self.engine.connect() as conn:
            for table_name, query in checks.items():
                result = pd.read_sql(query, conn)
                count = result['cnt'].iloc[0]
                print(f"{table_name:25} | {count:8} rows")
        
        print("\nWarehouse load complete!")


def main():
    loader = WarehouseLoader(DB_URL)
    loader.load_all()


if __name__ == "__main__":
    main()
