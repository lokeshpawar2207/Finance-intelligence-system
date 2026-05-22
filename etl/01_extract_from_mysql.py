"""
ETL Script 1: Extract data from SQL dump file
Purpose: Parse the provided .sql dump and extract all 7 tables into pandas DataFrames
Output: CSV files in data/raw/

Tables to extract:
- companies
- analysis
- balancesheet
- profitandloss
- cashflow
- prosandcons
- documents
"""

import re
import os
import pandas as pd
from pathlib import Path

# Create output directory
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

class SQLDumpParser:
    """Parse INSERT statements from SQL dump file"""
    
    def __init__(self, sql_file):
        self.sql_file = sql_file
        self.tables = {}
        
    def read_file(self):
        """Read SQL dump file"""
        with open(self.sql_file, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def extract_table_structure(self, sql_content, table_name):
        """Extract CREATE TABLE statement to determine columns"""
        pattern = rf"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?{table_name}`?\s*\((.*?)\);"
        match = re.search(pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            structure = match.group(1)
            # Extract column names (first word before whitespace/comma)
            columns = re.findall(r'`?(\w+)`?\s+', structure)
            return columns[:20]  # Limit to reasonable number
        return None
    
    def extract_insert_data(self, sql_content, table_name):
        """Extract INSERT INTO statements for a specific table"""
        pattern = rf"INSERT INTO\s+(?:IF NOT EXISTS\s+)?`?{table_name}`?\s*\(([^)]+)\)\s*VALUES\s*(.*?)(?=INSERT INTO|$)"
        matches = re.finditer(pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        all_rows = []
        
        for match in matches:
            columns_str = match.group(1)
            values_str = match.group(2)
            
            # Parse column names
            columns = [col.strip().strip('`') for col in columns_str.split(',')]
            
            # Parse VALUES tuples: (value1, value2, ...)
            # Handle escaped quotes and NULL values
            value_tuples = re.findall(r'\((.*?)\)(?:,|\s|$)', values_str, re.DOTALL)
            
            for value_tuple in value_tuples:
                values = self._parse_values(value_tuple)
                if len(values) == len(columns):
                    all_rows.append(dict(zip(columns, values)))
        
        return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
    
    def _parse_values(self, values_str):
        """Parse a single VALUES tuple, handling quotes and escapes"""
        values = []
        current = ""
        in_quotes = False
        escape_next = False
        
        for char in values_str:
            if escape_next:
                current += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == "'" and not escape_next:
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            values.append(current.strip())
        
        # Clean up quotes and NULL
        cleaned = []
        for val in values:
            val = val.strip()
            if val.upper() == 'NULL':
                cleaned.append(None)
            elif val.startswith("'") and val.endswith("'"):
                cleaned.append(val[1:-1])
            elif val.startswith('"') and val.endswith('"'):
                cleaned.append(val[1:-1])
            else:
                cleaned.append(val)
        
        return cleaned
    
    def parse(self):
        """Main parsing method"""
        sql_content = self.read_file()
        
        tables_to_extract = [
            'companies',
            'analysis',
            'balancesheet',
            'profitandloss',
            'cashflow',
            'prosandcons',
            'documents'
        ]
        
        for table_name in tables_to_extract:
            print(f"Extracting {table_name}...")
            df = self.extract_insert_data(sql_content, table_name)
            
            if not df.empty:
                self.tables[table_name] = df
                output_file = RAW_DATA_DIR / f"{table_name}.csv"
                df.to_csv(output_file, index=False)
                print(f"  ✓ Extracted {len(df)} rows, {len(df.columns)} columns")
                print(f"  ✓ Saved to {output_file}")
            else:
                print(f"  ✗ No data found for {table_name}")
        
        return self.tables


def main():
    """Main ETL entry point"""
    # Find SQL dump file
    sql_files = list(Path(".").glob("**/*.sql"))
    
    if not sql_files:
        print("ERROR: No .sql file found in project directory")
        print("Please provide the scriptticker.sql file")
        return
    
    sql_file = sql_files[0]
    print(f"Found SQL dump: {sql_file}")
    print(f"Parsing {sql_file.name}...\n")
    
    parser = SQLDumpParser(str(sql_file))
    tables = parser.parse()
    
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    for table_name, df in tables.items():
        print(f"{table_name:20} | Rows: {len(df):6} | Cols: {len(df.columns)}")
    
    print("\nAll raw data saved to data/raw/")
    print("Next step: Run 02_clean_and_transform.py")


if __name__ == "__main__":
    main()
