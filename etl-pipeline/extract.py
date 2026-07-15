from pathlib import Path
import pandas as pd

# -----------------------------
# Configuration
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Find the first CSV or Excel file in data/raw
data_files = list(RAW_DATA_DIR.glob("*.csv")) + list(RAW_DATA_DIR.glob("*.xlsx"))

if not data_files:
    raise FileNotFoundError(
        f"No CSV or XLSX file found in {RAW_DATA_DIR.resolve()}"
    )

data_file = data_files[0]

# -----------------------------
# Load dataset
# -----------------------------
if data_file.suffix == ".csv":
    df = pd.read_csv(data_file)
elif data_file.suffix == ".xlsx":
    df = pd.read_excel(data_file)

print(f"Loaded dataset: {data_file.name}")
print(f"Shape: {df.shape}")

# Preview
print(df.head())