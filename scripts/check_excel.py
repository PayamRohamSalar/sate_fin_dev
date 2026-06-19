import pandas as pd
import sys

df = pd.read_excel('data/University.xlsx')

# Write to file to avoid console encoding issues
output_path = 'data/excel_info.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"Total rows: {len(df)}\n")
    f.write(f"Total columns: {len(df.columns)}\n\n")
    f.write("Column names:\n")
    for i, col in enumerate(df.columns):
        f.write(f"  {i}: {col}\n")
    
    f.write("\n\nFirst 5 rows sample:\n")
    f.write(df.head(5).to_string())
    
    f.write("\n\nData types:\n")
    f.write(str(df.dtypes))

print(f"Information written to {output_path}")
