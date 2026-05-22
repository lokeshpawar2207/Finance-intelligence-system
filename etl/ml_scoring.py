"""
ML Health Scoring Module
Computes 8-dimensional health scores for all Nifty 100 companies
Runs weekly to update fact_ml_scores table
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://bluestock_user:bluestock_pass@localhost:5432/bluestock_dw'
)

class HealthScorer:
    """Compute ML-based health scores for companies"""
    
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.run_timestamp = datetime.now()
    
    def get_latest_financials(self):
        """Fetch latest financial data for all companies"""
        query = """
        SELECT 
            c.symbol,
            c.company_name,
            pl.sales,
            pl.net_profit,
            pl.operating_profit,
            pl.opm_pct,
            pl.eps,
            pl.net_profit_margin_pct,
            pl.interest_coverage,
            pl.dividend_payout_pct,
            bs.total_assets,
            bs.equity_capital,
            bs.reserves,
            bs.borrowings,
            bs.debt_to_equity,
            cf.operating_activity,
            cf.free_cash_flow,
            cf.cash_conversion_ratio,
            a.compounded_sales_growth_pct as growth_3y,
            a.stock_price_cagr_pct
        FROM dim_company c
        LEFT JOIN fact_profit_loss pl ON c.symbol = pl.symbol 
            AND pl.year_id = (
                SELECT year_id FROM dim_year 
                WHERE is_ttm = true LIMIT 1
            )
        LEFT JOIN fact_balance_sheet bs ON c.symbol = bs.symbol 
            AND bs.year_id = pl.year_id
        LEFT JOIN fact_cash_flow cf ON c.symbol = cf.symbol 
            AND cf.year_id = pl.year_id
        LEFT JOIN fact_analysis a ON c.symbol = a.symbol 
            AND a.period_label = '3Y'
        ORDER BY c.symbol
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        return df
    
    def score_profitability(self, df):
        """
        Score 1: Profitability (0-100)
        - OPM% (40%)
        - Net Margin% (30%)
        - ROE/Return (30%)
        """
        scores = pd.Series(0.0, index=df.index)
        
        # OPM% scoring: 0% = 0, 20% = 50, 30%+ = 100
        opm = df['opm_pct'].fillna(0)
        opm_score = np.minimum((opm / 30) * 100, 100)
        scores += opm_score * 0.40
        
        # Net Margin% scoring: 0% = 0, 10% = 50, 20%+ = 100
        net_margin = df['net_profit_margin_pct'].fillna(0)
        margin_score = np.minimum((net_margin / 20) * 100, 100)
        scores += margin_score * 0.30
        
        # ROE implicit in returns (higher EPS growth = higher returns)
        eps = df['eps'].fillna(0)
        eps_score = np.minimum((eps / eps[eps > 0].quantile(0.75, interpolation='linear')) * 100, 100) if eps.max() > 0 else 0
        scores += eps_score * 0.30
        
        return scores.round(2)
    
    def score_growth(self, df):
        """
        Score 2: Growth (0-100)
        - 3Y Sales CAGR (50%)
        - 3Y Profit Growth (50%)
        """
        scores = pd.Series(0.0, index=df.index)
        
        # Sales growth: 0% = 0, 10% = 50, 20%+ = 100
        growth_3y = df['growth_3y'].fillna(0)
        growth_score = np.minimum((growth_3y / 20) * 100, 100)
        scores += growth_score * 0.5
        
        # Stock CAGR: 0% = 0, 15% = 50, 30%+ = 100
        cagr = df['stock_price_cagr_pct'].fillna(0)
        cagr_score = np.minimum((cagr / 30) * 100, 100)
        scores += cagr_score * 0.5
        
        return scores.round(2)
    
    def score_leverage(self, df):
        """
        Score 3: Leverage & Solvency (0-100)
        - Debt-to-Equity (50%)
        - Interest Coverage (50%)
        Inverse scoring: Lower debt = higher score
        """
        scores = pd.Series(100.0, index=df.index)
        
        # D/E scoring: 0 = 100, 1 = 50, 2+ = 0
        de = df['debt_to_equity'].fillna(0)
        de_score = np.maximum(100 - (de * 50), 0)
        scores = scores * 0.0 + de_score * 0.5
        
        # Interest coverage: <2 = 0, 2-3 = 50, 3+ = 100
        int_cov = df['interest_coverage'].fillna(0)
        int_cov_score = np.minimum((int_cov / 3) * 100, 100)
        scores += int_cov_score * 0.5
        
        return scores.round(2)
    
    def score_cashflow(self, df):
        """
        Score 4: Cash Flow Quality (0-100)
        - Operating Cash Flow (50%)
        - Cash Conversion Ratio (50%)
        """
        scores = pd.Series(0.0, index=df.index)
        
        # Operating cash flow (positive is good)
        ocf = df['operating_activity'].fillna(0)
        ocf_positive = (ocf > 0).astype(int) * 50
        scores += ocf_positive
        
        # Cash conversion: 0.5-1.5 = good (100), <0.5 = warning, >1.5 = excellent
        ccr = df['cash_conversion_ratio'].fillna(0)
        ccr_score = np.minimum((ccr / 1.5) * 100, 100)
        ccr_score = np.where(ccr > 0, ccr_score, 0)
        scores += ccr_score * 0.5
        
        return scores.round(2)
    
    def score_dividend(self, df):
        """
        Score 5: Dividend Consistency (0-100)
        - Payout ratio (50%)
        - Consistency (50%)
        Income investors prefer stable, growing dividends
        """
        scores = pd.Series(0.0, index=df.index)
        
        # Payout ratio: 0-50% = good (100), >50% = risky
        payout = df['dividend_payout_pct'].fillna(0)
        payout_score = np.where(payout <= 50, 100, np.maximum(100 - (payout - 50), 0))
        scores += payout_score * 0.5
        
        # If paying dividend: 50 points, if not: 0 points (then other 50% goes to growth)
        has_dividend = (payout > 0).astype(int) * 100
        scores += has_dividend * 0.5
        
        return scores.round(2)
    
    def score_trend(self, df):
        """
        Score 6: Trend & Momentum (0-100)
        Currently simplified: based on growth trajectory
        In production, would look at YoY changes
        """
        scores = pd.Series(50.0, index=df.index)  # Default to neutral
        
        # Positive growth = upward trend
        growth_3y = df['growth_3y'].fillna(0)
        trend_boost = np.where(growth_3y > 10, 25, np.where(growth_3y < 0, -25, 0))
        scores += trend_boost
        
        return scores.round(2)
    
    def compute_all_scores(self):
        """Compute all 8 health dimensions"""
        print("Fetching latest financial data...")
        df = self.get_latest_financials()
        
        print("Computing health scores...")
        
        df['profitability_score'] = self.score_profitability(df)
        df['growth_score'] = self.score_growth(df)
        df['leverage_score'] = self.score_leverage(df)
        df['cashflow_score'] = self.score_cashflow(df)
        df['dividend_score'] = self.score_dividend(df)
        df['trend_score'] = self.score_trend(df)
        
        # Overall score: average of 6 dimensions
        score_cols = [
            'profitability_score', 'growth_score', 'leverage_score',
            'cashflow_score', 'dividend_score', 'trend_score'
        ]
        df['overall_score'] = df[score_cols].mean(axis=1).round(2)
        
        # Determine health label
        def get_label(score):
            if score >= 85:
                return 1  # EXCELLENT
            elif score >= 70:
                return 2  # GOOD
            elif score >= 50:
                return 3  # AVERAGE
            elif score >= 35:
                return 4  # WEAK
            else:
                return 5  # POOR
        
        df['health_label_id'] = df['overall_score'].apply(get_label)
        
        return df
    
    def save_scores(self, scores_df):
        """Save computed scores to database"""
        print(f"Saving {len(scores_df)} health scores to database...")
        
        with self.engine.connect() as conn:
            for _, row in scores_df.iterrows():
                upsert_sql = text("""
                    INSERT INTO fact_ml_scores 
                    (symbol, computed_at, overall_score, profitability_score, growth_score,
                     leverage_score, cashflow_score, dividend_score, trend_score, health_label_id)
                    VALUES 
                    (:symbol, :computed_at, :overall_score, :profitability_score, :growth_score,
                     :leverage_score, :cashflow_score, :dividend_score, :trend_score, :health_label_id)
                    ON CONFLICT DO NOTHING
                """)
                
                try:
                    conn.execute(upsert_sql, {
                        'symbol': row['symbol'],
                        'computed_at': self.run_timestamp,
                        'overall_score': float(row['overall_score']) if row['overall_score'] else None,
                        'profitability_score': float(row['profitability_score']) if row['profitability_score'] else None,
                        'growth_score': float(row['growth_score']) if row['growth_score'] else None,
                        'leverage_score': float(row['leverage_score']) if row['leverage_score'] else None,
                        'cashflow_score': float(row['cashflow_score']) if row['cashflow_score'] else None,
                        'dividend_score': float(row['dividend_score']) if row['dividend_score'] else None,
                        'trend_score': float(row['trend_score']) if row['trend_score'] else None,
                        'health_label_id': int(row['health_label_id']) if row['health_label_id'] else None,
                    })
                except Exception as e:
                    print(f"  Warning: {row['symbol']} — {e}")
            
            conn.commit()
        
        print("✓ Health scores saved")
    
    def generate_report(self, scores_df):
        """Print summary report"""
        print("\n" + "="*70)
        print("HEALTH SCORE REPORT")
        print("="*70)
        print(f"Run timestamp: {self.run_timestamp}")
        print(f"Companies scored: {len(scores_df[scores_df['overall_score'].notna()])}")
        
        scores = scores_df['overall_score'].dropna()
        print(f"\nScore Distribution:")
        print(f"  Average: {scores.mean():.1f}")
        print(f"  Median:  {scores.median():.1f}")
        print(f"  Min:     {scores.min():.1f}")
        print(f"  Max:     {scores.max():.1f}")
        
        label_map = {1: 'EXCELLENT', 2: 'GOOD', 3: 'AVERAGE', 4: 'WEAK', 5: 'POOR'}
        print(f"\nCompanies by Health Label:")
        for label_id, label_name in label_map.items():
            count = (scores_df['health_label_id'] == label_id).sum()
            print(f"  {label_name:10} — {count:3} companies")
        
        # Top 5 and Bottom 5
        top5 = scores_df.nlargest(5, 'overall_score')[['symbol', 'company_name', 'overall_score']]
        bottom5 = scores_df.nsmallest(5, 'overall_score')[['symbol', 'company_name', 'overall_score']]
        
        print(f"\nTop 5 Companies:")
        for _, row in top5.iterrows():
            print(f"  {row['symbol']:15} {row['company_name']:30} {row['overall_score']:6.1f}")
        
        print(f"\nBottom 5 Companies:")
        for _, row in bottom5.iterrows():
            print(f"  {row['symbol']:15} {row['company_name']:30} {row['overall_score']:6.1f}")
        
        print("="*70)


def main():
    """Run health scoring"""
    scorer = HealthScorer(DB_URL)
    
    # Compute scores
    scores_df = scorer.compute_all_scores()
    
    # Save to database
    scorer.save_scores(scores_df)
    
    # Generate report
    scorer.generate_report(scores_df)
    
    print("\nNext step: Power BI dashboards will automatically pick up latest scores")


if __name__ == "__main__":
    main()
