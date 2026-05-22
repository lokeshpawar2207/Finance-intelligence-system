"""
Exploratory Data Analysis (EDA) for Nifty 100 Companies
To use: Convert to Jupyter notebook and run cell by cell

jupyter nbconvert --to notebook 01_eda_nifty100.py
"""

# ============================================================================
# Cell 1: Setup and Imports
# ============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()
DB_URL = os.getenv('DATABASE_URL', 'postgresql://bluestock_user:bluestock_pass@localhost:5432/bluestock_dw')
engine = create_engine(DB_URL)

# Matplotlib settings
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("✓ Setup complete. Connected to Bluestock warehouse.")

# ============================================================================
# Cell 2: Load Data
# ============================================================================

# Companies
query_companies = """
SELECT c.symbol, c.company_name, s.sector_name, c.sub_sector
FROM dim_company c
LEFT JOIN dim_sector s ON c.sector_id = s.sector_id
ORDER BY c.symbol
"""
companies = pd.read_sql(query_companies, engine)
print(f"Companies loaded: {len(companies)} records")
print(companies.head(10))

# ============================================================================
# Cell 3: Latest Financial Data
# ============================================================================

query_latest = """
SELECT 
    c.symbol,
    c.company_name,
    s.sector_name,
    pl.sales,
    pl.net_profit,
    pl.opm_pct,
    pl.eps,
    bs.total_assets,
    bs.debt_to_equity,
    cf.operating_activity
FROM dim_company c
LEFT JOIN dim_sector s ON c.sector_id = s.sector_id
LEFT JOIN fact_profit_loss pl ON c.symbol = pl.symbol 
    AND pl.year_id = (SELECT year_id FROM dim_year WHERE is_ttm = true LIMIT 1)
LEFT JOIN fact_balance_sheet bs ON c.symbol = bs.symbol AND bs.year_id = pl.year_id
LEFT JOIN fact_cash_flow cf ON c.symbol = cf.symbol AND cf.year_id = pl.year_id
WHERE pl.sales IS NOT NULL
ORDER BY c.symbol
"""
latest_data = pd.read_sql(query_latest, engine)
print(f"\nLatest financial data: {len(latest_data)} companies with data")
print(latest_data.describe())

# ============================================================================
# Cell 4: Sector-Level Analysis
# ============================================================================

sector_summary = latest_data.groupby('sector_name').agg({
    'symbol': 'count',
    'sales': 'sum',
    'net_profit': 'sum',
    'opm_pct': 'mean',
    'debt_to_equity': 'mean'
}).round(2)
sector_summary.columns = ['Company Count', 'Total Sales', 'Total Profit', 'Avg OPM%', 'Avg D/E']
sector_summary = sector_summary.sort_values('Total Sales', ascending=False)
print("\nSector Summary:")
print(sector_summary)

# ============================================================================
# Cell 5: Profitability Analysis
# ============================================================================

# OPM% Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(latest_data['opm_pct'].dropna(), bins=30, color='skyblue', edgecolor='black')
axes[0].set_xlabel('Operating Profit Margin %')
axes[0].set_ylabel('Number of Companies')
axes[0].set_title('OPM% Distribution (All Companies)')
axes[0].axvline(latest_data['opm_pct'].mean(), color='red', linestyle='--', label=f'Mean: {latest_data["opm_pct"].mean():.1f}%')
axes[0].legend()

# By Sector
sector_opm = latest_data.groupby('sector_name')['opm_pct'].mean().sort_values(ascending=False)
sector_opm.plot(kind='barh', ax=axes[1], color='lightcoral')
axes[1].set_xlabel('Average OPM%')
axes[1].set_title('Profitability by Sector')

plt.tight_layout()
plt.show()

# ============================================================================
# Cell 6: Growth Analysis
# ============================================================================

query_growth = """
SELECT 
    c.symbol,
    c.company_name,
    s.sector_name,
    a.period_label,
    a.compounded_sales_growth_pct,
    a.stock_price_cagr_pct
FROM dim_company c
LEFT JOIN dim_sector s ON c.sector_id = s.sector_id
LEFT JOIN fact_analysis a ON c.symbol = a.symbol
WHERE a.period_label IN ('3Y', '5Y', '10Y')
ORDER BY c.symbol, a.period_label
"""
growth_data = pd.read_sql(query_growth, engine)

# 3Y CAGR Analysis
growth_3y = growth_data[growth_data['period_label'] == '3Y'].dropna(subset=['compounded_sales_growth_pct'])
print(f"\n3-Year Sales CAGR Statistics:")
print(growth_3y['compounded_sales_growth_pct'].describe())

# Top 10 Growth Companies
top_growth = growth_3y.nlargest(10, 'compounded_sales_growth_pct')[['symbol', 'company_name', 'sector_name', 'compounded_sales_growth_pct']]
print("\nTop 10 Companies by 3Y Sales CAGR:")
print(top_growth)

# ============================================================================
# Cell 7: Leverage Analysis
# ============================================================================

# D/E Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Distribution
de_data = latest_data['debt_to_equity'].dropna()
axes[0].hist(de_data, bins=30, color='lightyellow', edgecolor='black')
axes[0].axvline(1.0, color='red', linestyle='--', label='D/E = 1.0 (Threshold)', linewidth=2)
axes[0].set_xlabel('Debt-to-Equity Ratio')
axes[0].set_ylabel('Number of Companies')
axes[0].set_title('D/E Distribution')
axes[0].legend()

# High Leverage Companies
high_leverage = latest_data[latest_data['debt_to_equity'] > 2].nlargest(10, 'debt_to_equity')[['symbol', 'company_name', 'sector_name', 'debt_to_equity']]
print(f"\nCompanies with High Leverage (D/E > 2.0):")
print(high_leverage)

# Debt-Free Companies
debt_free = latest_data[latest_data['debt_to_equity'] < 0.1]
print(f"\nDebt-Free or Low-Leverage Companies: {len(debt_free)}")
print(debt_free[['symbol', 'company_name', 'sector_name']].head(10))

# ============================================================================
# Cell 8: Size vs Profitability
# ============================================================================

# Scatter: Sales vs OPM%
fig, ax = plt.subplots(figsize=(12, 7))
scatter = ax.scatter(
    latest_data['sales'] / 1000,  # Convert to thousands
    latest_data['opm_pct'],
    s=100,
    alpha=0.6,
    c=pd.Categorical(latest_data['sector_name']).codes,
    cmap='tab20'
)
ax.set_xlabel('Total Sales (Thousands Crores)')
ax.set_ylabel('Operating Profit Margin %')
ax.set_title('Company Size vs Profitability')
ax.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax, label='Sector')
plt.tight_layout()
plt.show()

# ============================================================================
# Cell 9: Health Score Distribution (if available)
# ============================================================================

query_health = """
SELECT 
    symbol,
    company_name,
    overall_score,
    profitability_score,
    growth_score,
    leverage_score,
    cashflow_score,
    dividend_score,
    health_label_id
FROM (
    SELECT DISTINCT ON (symbol) *
    FROM fact_ml_scores
    ORDER BY symbol, computed_at DESC
) latest
WHERE overall_score IS NOT NULL
ORDER BY overall_score DESC
"""

try:
    health_scores = pd.read_sql(query_health, engine)
    
    print(f"\nHealth Scores Available: {len(health_scores)} companies")
    print(health_scores[['symbol', 'company_name', 'overall_score']].head(10))
    
    # Distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(health_scores['overall_score'], bins=20, color='steelblue', edgecolor='black')
    ax.axvline(health_scores['overall_score'].mean(), color='red', linestyle='--', label=f'Mean: {health_scores["overall_score"].mean():.1f}')
    ax.set_xlabel('Health Score (0-100)')
    ax.set_ylabel('Number of Companies')
    ax.set_title('Health Score Distribution')
    ax.legend()
    plt.tight_layout()
    plt.show()
    
except Exception as e:
    print(f"Health scores not yet available: {e}")

# ============================================================================
# Cell 10: Summary Statistics
# ============================================================================

print("\n" + "="*70)
print("NIFTY 100 EDA SUMMARY")
print("="*70)
print(f"Total Companies: {len(companies)}")
print(f"Companies with Financial Data: {len(latest_data)}")
print(f"Sectors: {companies['sector_name'].nunique()}")
print(f"\nData Quality:")
print(f"  Sales: {latest_data['sales'].notna().sum()} records")
print(f"  Net Profit: {latest_data['net_profit'].notna().sum()} records")
print(f"  OPM%: {latest_data['opm_pct'].notna().sum()} records")
print(f"  D/E Ratio: {latest_data['debt_to_equity'].notna().sum()} records")

print("\nKey Insights:")
print(f"  Avg OPM%: {latest_data['opm_pct'].mean():.1f}%")
print(f"  Avg D/E: {latest_data['debt_to_equity'].mean():.2f}")
print(f"  Total Sector Revenue: ₹{latest_data['sales'].sum():,.0f} Cr")
print(f"  Total Sector Profit: ₹{latest_data['net_profit'].sum():,.0f} Cr")
print("="*70)
