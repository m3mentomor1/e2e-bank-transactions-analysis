from pathlib import Path

import pandas as pd

# -----------------------------
# Configuration
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract(raw_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Load the first CSV or Excel file from data/raw."""
    data_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.xlsx"))

    if not data_files:
        raise FileNotFoundError(
            f"No CSV or XLSX file found in {raw_dir.resolve()}"
        )

    data_file = data_files[0]

    if data_file.suffix == ".csv":
        df = pd.read_csv(data_file)
    elif data_file.suffix == ".xlsx":
        df = pd.read_excel(data_file)
    else:
        raise ValueError(f"Unsupported file type: {data_file.suffix}")

    print(f"Loaded dataset: {data_file.name}")
    print(f"Shape: {df.shape}")
    return df


# -----------------------------
# Run extract
# -----------------------------
if __name__ == "__main__":
    df = extract()
    print(df.head())
