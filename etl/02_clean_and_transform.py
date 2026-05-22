"""
ETL Script 2: Clean and standardize raw data
Purpose: Normalize year formats, parse analysis strings, handle nulls, classify sectors
Output: CSV files in data/clean/ + sector_mapping.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime

RAW_DATA_DIR = Path("data/raw")
CLEAN_DATA_DIR = Path("data/clean")
CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Sector mapping for all 100 Nifty companies
SECTOR_MAPPING = {
    # IT Services
    'TCS': ('IT Services', 'Software'),
    'INFY': ('IT Services', 'Software'),
    'WIPRO': ('IT Services', 'Software'),
    'HCLT': ('IT Services', 'Software'),
    'TECHM': ('IT Services', 'Software'),
    'LTTS': ('IT Services', 'Software'),
    'MPHASIS': ('IT Services', 'Software'),
    'PERSISTENT': ('IT Services', 'Software'),
    'LTIM': ('IT Services', 'Software'),
    
    # Banking
    'HDFCBANK': ('Banking', 'Private Banking'),
    'AXISBANK': ('Banking', 'Private Banking'),
    'ICICIBANK': ('Banking', 'Private Banking'),
    'INDUSIND': ('Banking', 'Private Banking'),
    'BANKBARODA': ('Banking', 'Public Banking'),
    'SBIN': ('Banking', 'Public Banking'),
    'PNB': ('Banking', 'Public Banking'),
    'CENTRALBANK': ('Banking', 'Public Banking'),
    'UNIONBANK': ('Banking', 'Public Banking'),
    'CANBANK': ('Banking', 'Public Banking'),
    
    # NBFC & Finance
    'BAJFINANCE': ('NBFC', 'Non-Banking Finance'),
    'BAJAJFINSV': ('NBFC', 'Non-Banking Finance'),
    'HDFC': ('NBFC', 'Housing Finance'),
    'LT': ('NBFC', 'Financial Holding'),
    'SUNPHARMA': ('NBFC', 'Healthcare Finance'),
    
    # Insurance
    'SBILIFE': ('Insurance', 'Life Insurance'),
    'HDFCLIFE': ('Insurance', 'Life Insurance'),
    'ICICIPRULI': ('Insurance', 'Life Insurance'),
    
    # Energy & Power
    'ADANIGREEN': ('Energy', 'Renewable Energy'),
    'ADANIPOWER': ('Energy', 'Power Generation'),
    'ADANIENSOL': ('Energy', 'Renewable Energy'),
    'ATGL': ('Energy', 'Gas Utilities'),
    'NTPC': ('Energy', 'Power Generation'),
    'POWERGRID': ('Energy', 'Power Distribution'),
    'RELIANCE': ('Energy', 'Oil & Gas'),
    
    # Cement
    'AMBUJACEM': ('Cement', 'Cement Manufacturing'),
    'SHREECEM': ('Cement', 'Cement Manufacturing'),
    'APOLLOHOSP': ('Cement', 'Cement Manufacturing'),
    'JKCEMENT': ('Cement', 'Cement Manufacturing'),
    'GRASIM': ('Cement', 'Cement Manufacturing'),
    
    # Pharma & Healthcare
    'SUNPHARMA': ('Healthcare', 'Pharmaceutical'),
    'DIVI': ('Healthcare', 'Pharmaceutical'),
    'APOLLOHOSP': ('Healthcare', 'Hospital Services'),
    'CIPLA': ('Healthcare', 'Pharmaceutical'),
    'LUPIN': ('Healthcare', 'Pharmaceutical'),
    'DRREDDY': ('Healthcare', 'Pharmaceutical'),
    'BIOCON': ('Healthcare', 'Pharmaceutical'),
    'ALKEM': ('Healthcare', 'Pharmaceutical'),
    'AUROPHARMA': ('Healthcare', 'Pharmaceutical'),
    
    # Auto
    'BAJAJ-AUTO': ('Auto', 'Two-Wheeler'),
    'MARUTI': ('Auto', 'Four-Wheeler'),
    'HEROMOTOCO': ('Auto', 'Two-Wheeler'),
    'TATAMOTORS': ('Auto', 'Four-Wheeler'),
    'EICHERMOT': ('Auto', 'Two-Wheeler'),
    'BHEL': ('Auto', 'Auto Components'),
    'ASHOK': ('Auto', 'Commercial Vehicle'),
    'TATACOMM': ('Auto', 'Logistic Infrastructure'),
    
    # Paint & Chemicals
    'ASIANPAINT': ('Paint', 'Paint Manufacturing'),
    'PIDILITIND': ('Paint', 'Chemicals'),
    'BASF': ('Paint', 'Chemicals'),
    'SCI': ('Paint', 'Specialty Chemicals'),
    
    # Consumer Goods & FMCG
    'NESTLEIND': ('Consumer Goods', 'FMCG'),
    'ITC': ('Consumer Goods', 'FMCG'),
    'HUL': ('Consumer Goods', 'FMCG'),
    'BRITANNIA': ('Consumer Goods', 'FMCG'),
    'MARICO': ('Consumer Goods', 'FMCG'),
    'GODREJIND': ('Consumer Goods', 'FMCG'),
    'DABUR': ('Consumer Goods', 'FMCG'),
    'COLPAL': ('Consumer Goods', 'FMCG'),
    'BSOFT': ('Consumer Goods', 'Software'),
    'BOSCHLTD': ('Consumer Goods', 'Auto Components'),
    'BEL': ('Consumer Goods', 'Defense'),
    'BLUESTARCO': ('Consumer Goods', 'Electronics'),
    'CGPOWER': ('Consumer Goods', 'Electrical Equipment'),
    'CROMPTON': ('Consumer Goods', 'Electrical Equipment'),
    'GRPL': ('Consumer Goods', 'Logistics'),
    'MUTHOOTFIN': ('Consumer Goods', 'Finance'),
    'IRCTC': ('Consumer Goods', 'Tourism & Transport'),
    'IOC': ('Consumer Goods', 'Oil & Gas'),
    'JSWSTEEL': ('Consumer Goods', 'Steel'),
    'JINDALSTEL': ('Consumer Goods', 'Steel'),
    'TISCO': ('Consumer Goods', 'Steel'),
    'SAIL': ('Consumer Goods', 'Steel'),
    'NMDC': ('Consumer Goods', 'Mining'),
    'COAL': ('Consumer Goods', 'Mining'),
    'HINDALCO': ('Consumer Goods', 'Aluminum'),
    'VEDL': ('Consumer Goods', 'Mining & Metals'),
    'JSWINDIA': ('Consumer Goods', 'Engineering'),
    'KIRLOSENG': ('Consumer Goods', 'Pumps'),
    'L&TFH': ('Consumer Goods', 'Finance'),
    'SUNHARMA': ('Consumer Goods', 'Pharmaceutical'),
    'GAIL': ('Consumer Goods', 'Oil & Gas'),
    'OIL': ('Consumer Goods', 'Oil & Gas'),
    'ONGC': ('Consumer Goods', 'Oil & Gas'),
    'DCP': ('Consumer Goods', 'Petroleum'),
    'ENGINERSIN': ('Consumer Goods', 'Engineering'),
    'EXIDEIND': ('Consumer Goods', 'Batteries'),
    'FEDERALBNK': ('Consumer Goods', 'Banking'),
    'GRAPHITE': ('Consumer Goods', 'Graphite'),
    'HDFCAMC': ('Consumer Goods', 'Asset Management'),
    'HAL': ('Consumer Goods', 'Defense'),
    'HONAUT': ('Consumer Goods', 'Automobiles'),
    'IPCALAB': ('Consumer Goods', 'Pharmaceutical'),
    'IFBIND': ('Consumer Goods', 'Appliances'),
    'KPITTECH': ('Consumer Goods', 'Software'),
    'KSCBANK': ('Consumer Goods', 'Banking'),
    'MANAPPURAM': ('Consumer Goods', 'Finance'),
    'M&MFIN': ('Consumer Goods', 'Finance'),
    'MAXHEALTH': ('Consumer Goods', 'Healthcare'),
    'METROPOLIS': ('Consumer Goods', 'Healthcare'),
    'MINDTREE': ('Consumer Goods', 'IT Services'),
    'MRF': ('Consumer Goods', 'Tires'),
    'NAM-INDIA': ('Consumer Goods', 'FMCG'),
    'NATIONALUM': ('Consumer Goods', 'Aluminum'),
    'NAUKRI': ('Consumer Goods', 'Internet'),
    'NORTHMONDA': ('Consumer Goods', 'Insurance'),
    'PAGEIND': ('Consumer Goods', 'Batteries'),
    'PCJEWELLER': ('Consumer Goods', 'Jewelry'),
    'PIIND': ('Consumer Goods', 'Chemicals'),
    'RBLBANK': ('Consumer Goods', 'Banking'),
    'RATNAMANI': ('Consumer Goods', 'Metal Products'),
    'REDINGTON': ('Consumer Goods', 'Distribution'),
    'RELAXO': ('Consumer Goods', 'Footwear'),
    'RENUKA': ('Consumer Goods', 'Sugar'),
    'RHIM': ('Consumer Goods', 'Housing Finance'),
    'RITES': ('Consumer Goods', 'Railways'),
    'SARTOG': ('Consumer Goods', 'Construction'),
    'SAURENERGI': ('Consumer Goods', 'Power'),
    'SBIADMINS': ('Consumer Goods', 'Financial Services'),
    'SEGMENTTOL': ('Consumer Goods', 'Construction'),
    'SHRIRAMFIN': ('Consumer Goods', 'Finance'),
    'SKFINDIA': ('Consumer Goods', 'Bearing'),
    'SMARTLINK': ('Consumer Goods', 'Infrastructure'),
    'SPCBANK': ('Consumer Goods', 'Banking'),
    'SUMICHEM': ('Consumer Goods', 'Chemicals'),
    'SUZLON': ('Consumer Goods', 'Renewable Energy'),
    'SYNGENE': ('Consumer Goods', 'Contract Research'),
    'TATASTEEL': ('Consumer Goods', 'Steel'),
    'TATASTL': ('Consumer Goods', 'Steel'),
    'TEAMLEASE': ('Consumer Goods', 'HR Services'),
    'TIMKEN': ('Consumer Goods', 'Bearings'),
    'TORRENTPHARM': ('Consumer Goods', 'Pharmaceutical'),
    'UCOBANK': ('Consumer Goods', 'Banking'),
    'ULTRACEMCO': ('Consumer Goods', 'Cement'),
    'UNOMINDA': ('Consumer Goods', 'Distribution'),
    'VIKASMULTI': ('Consumer Goods', 'FMCG'),
    'VSTIND': ('Consumer Goods', 'Wires & Cables'),
    'WHIRLPOOL': ('Consumer Goods', 'Appliances'),
    'XCHANGERATE': ('Consumer Goods', 'Finance'),
    'YAMARTD': ('Consumer Goods', 'Motorcycles'),
    'ZEEL': ('Consumer Goods', 'Media'),
    'ZOMATO': ('Consumer Goods', 'Food Delivery'),
}

class DataCleaner:
    """Clean and transform raw data"""
    
    def __init__(self):
        self.cleaned_data = {}
    
    def standardize_year(self, year_str):
        """
        Standardize year formats:
        'Mar 2024', 'Mar-24', 'Mar 2013', '2024', 'TTM' → consistent format
        """
        if pd.isna(year_str):
            return None, None, None, False, 0
        
        year_str = str(year_str).strip().upper()
        
        if year_str == 'TTM':
            return 'TTM', None, True, False, 99999
        
        # Match patterns like "Mar 2024", "Mar-24", "Mar 2013"
        match = re.match(r'([A-Z]{3})\s*-?\s*(\d{2,4})', year_str)
        if match:
            month = match.group(1)
            year = match.group(2)
            
            # Convert 2-digit year to 4-digit
            if len(year) == 2:
                year = int(year)
                year = 2000 + year if year <= 30 else 1900 + year
            else:
                year = int(year)
            
            # Determine fiscal year (assume March FY: Mar 2024 = FY 2024)
            month_to_fiscal = {
                'JAN': year - 1, 'FEB': year - 1, 'MAR': year,
                'APR': year, 'MAY': year, 'JUN': year,
                'JUL': year, 'AUG': year, 'SEP': year,
                'OCT': year, 'NOV': year, 'DEC': year
            }
            fiscal_year = month_to_fiscal.get(month, year)
            
            year_label = f"{month} {year}"
            
            # Quarter mapping
            quarter_map = {
                'JAN': 'Q4', 'FEB': 'Q4', 'MAR': 'Q4',
                'APR': 'Q1', 'MAY': 'Q1', 'JUN': 'Q1',
                'JUL': 'Q2', 'AUG': 'Q2', 'SEP': 'Q2',
                'OCT': 'Q3', 'NOV': 'Q3', 'DEC': 'Q3'
            }
            quarter = quarter_map.get(month, 'Q4')
            
            # Sort order (descending by year, then by quarter)
            sort_order = (9999 - year) * 4 + (5 - int(quarter[1]))
            
            return year_label, fiscal_year, False, False, sort_order
        
        # Try direct year parse
        try:
            year = int(year_str)
            return str(year), year, False, False, 9999 - year
        except:
            return None, None, False, False, 0
    
    def parse_analysis_row(self, row):
        """
        Parse analysis table values: "10 Years: 11%" → ("10Y", 11.0)
        """
        parsed = {}
        for col in ['10_Years', '5_Years', '3_Years', 'TTM']:
            value = row.get(col)
            if pd.isna(value):
                parsed[col] = None
            else:
                val_str = str(value).strip()
                # Extract numeric value
                match = re.search(r'([-+]?\d+\.?\d*)', val_str)
                if match:
                    parsed[col] = float(match.group(1))
                else:
                    parsed[col] = None
        
        return parsed
    
    def clean_companies(self, df):
        """Clean companies table"""
        df = df.copy()
        
        # Clean company names
        df['company_name'] = df['company_name'].str.strip().str.replace(r'\r\n', '', regex=True)
        
        # Classify sectors using mapping
        df['sector'] = df['symbol'].map(lambda x: SECTOR_MAPPING.get(x, ('Unknown', 'Unknown'))[0])
        df['sub_sector'] = df['symbol'].map(lambda x: SECTOR_MAPPING.get(x, ('Unknown', 'Unknown'))[1])
        
        return df
    
    def clean_balancesheet(self, df):
        """Clean balance sheet"""
        df = df.copy()
        
        # Standardize years
        df[['year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']] = \
            df['year'].apply(lambda x: pd.Series(self.standardize_year(x)))
        
        # Convert numeric columns
        numeric_cols = [col for col in df.columns if col not in 
                       ['symbol', 'company_name', 'year', 'year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Compute derived metrics
        df['debt_to_equity'] = df['borrowings'] / (df['equity_capital'] + df['reserves'])
        df['equity_ratio'] = (df['equity_capital'] + df['reserves']) / df['total_assets']
        
        return df
    
    def clean_profitandloss(self, df):
        """Clean profit & loss"""
        df = df.copy()
        
        # Standardize years
        df[['year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']] = \
            df['year'].apply(lambda x: pd.Series(self.standardize_year(x)))
        
        # Convert numeric columns
        numeric_cols = [col for col in df.columns if col not in 
                       ['symbol', 'company_name', 'year', 'year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Compute derived metrics
        df['net_profit_margin_pct'] = (df['net_profit'] / df['sales'] * 100).round(2)
        df['expense_ratio_pct'] = (df['expenses'] / df['sales'] * 100).round(2)
        df['interest_coverage'] = (df['operating_profit'] / df['interest']).round(4)
        
        return df
    
    def clean_cashflow(self, df):
        """Clean cash flow"""
        df = df.copy()
        
        # Standardize years
        df[['year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']] = \
            df['year'].apply(lambda x: pd.Series(self.standardize_year(x)))
        
        # Convert numeric columns
        numeric_cols = [col for col in df.columns if col not in 
                       ['symbol', 'company_name', 'year', 'year_label', 'fiscal_year', 'is_ttm', 'is_half_year', 'sort_order']]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Compute derived metrics
        df['free_cash_flow'] = df['operating_activity'] + df['investing_activity']
        
        return df
    
    def clean_analysis(self, df):
        """Clean analysis (growth metrics)"""
        df = df.copy()
        
        # This is already in period format (10Y, 5Y, 3Y, TTM)
        numeric_cols = [col for col in df.columns if col not in ['symbol', 'company_name']]
        
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def clean_all(self):
        """Run all cleaning pipelines"""
        print("Starting data cleaning...\n")
        
        # Load raw CSVs
        tables = {
            'companies': RAW_DATA_DIR / 'companies.csv',
            'balancesheet': RAW_DATA_DIR / 'balancesheet.csv',
            'profitandloss': RAW_DATA_DIR / 'profitandloss.csv',
            'cashflow': RAW_DATA_DIR / 'cashflow.csv',
            'analysis': RAW_DATA_DIR / 'analysis.csv',
            'prosandcons': RAW_DATA_DIR / 'prosandcons.csv',
            'documents': RAW_DATA_DIR / 'documents.csv',
        }
        
        for table_name, file_path in tables.items():
            if not file_path.exists():
                print(f"SKIP: {table_name} not found")
                continue
            
            print(f"Cleaning {table_name}...")
            df = pd.read_csv(file_path)
            
            if table_name == 'companies':
                df = self.clean_companies(df)
            elif table_name == 'balancesheet':
                df = self.clean_balancesheet(df)
            elif table_name == 'profitandloss':
                df = self.clean_profitandloss(df)
            elif table_name == 'cashflow':
                df = self.clean_cashflow(df)
            elif table_name == 'analysis':
                df = self.clean_analysis(df)
            # prosandcons and documents: light cleaning only
            
            # Save cleaned
            output_file = CLEAN_DATA_DIR / f"{table_name}.csv"
            df.to_csv(output_file, index=False)
            print(f"  ✓ Saved {len(df)} rows to {output_file}\n")
        
        # Save sector mapping
        sector_df = pd.DataFrame([
            {'symbol': k, 'sector': v[0], 'sub_sector': v[1]}
            for k, v in SECTOR_MAPPING.items()
        ])
        sector_df.to_csv(CLEAN_DATA_DIR / 'sector_mapping.csv', index=False)
        print(f"✓ Sector mapping saved: {len(sector_df)} companies")


def main():
    cleaner = DataCleaner()
    cleaner.clean_all()
    print("\n" + "="*60)
    print("Data cleaning complete!")
    print("Next step: Run 03_load_to_warehouse.py")


if __name__ == "__main__":
    main()
