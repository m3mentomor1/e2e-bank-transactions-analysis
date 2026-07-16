from pathlib import Path
import sys

import pandas as pd

# Allow `python etl-pipeline/transform.py` from the project root
ETL_DIR = Path(__file__).resolve().parent
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

from extract import PROJECT_ROOT, extract

# -----------------------------
# Configuration
# -----------------------------
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

COLUMN_RENAME = {
    "Transaction Number": "transaction_number",
    "Transaction Date": "transaction_date",
    "Transaction Type": "transaction_type",
    "Transaction Description": "transaction_description",
    "Debit Amount": "debit_amount",
    "Credit Amount": "credit_amount",
    "Balance": "balance",
    "Category": "category",
    "Location City": "location_city",
    "Location Country": "location_country",
}

# Known location corrections found during EDA
COUNTRY_CORRECTIONS = {
    "Prague": "Czech Republic",
}


def parse_transaction_date(series: pd.Series) -> pd.Series:
    """
    Parse mixed date formats from Excel export.

    EDA finding: ~57% of dates are strings (DD/MM/YYYY) and
    ~43% are already datetime objects.
    """
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def clean_text(series: pd.Series) -> pd.Series:
    """Strip whitespace and collapse repeated internal spaces."""
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


def standardize_label_case(series: pd.Series) -> pd.Series:
    """
    Collapse case-only duplicates (e.g. Swansea vs swansea).

    Short alphabetic codes such as UK / USA stay uppercase.
    Longer labels use title case.
    """

    def _canonical(value):
        if pd.isna(value):
            return value

        text = str(value)
        compact = text.replace(" ", "")

        if compact.isalpha() and len(compact) <= 3:
            return text.upper()

        return text.title()

    return series.map(_canonical).astype("string")


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich the raw bank transaction data."""
    df = df.copy()

    # Standardize column names for downstream load / SQL usage
    df = df.rename(columns=COLUMN_RENAME)

    # Parse dates (mixed string + datetime from Excel)
    df["transaction_date"] = parse_transaction_date(df["transaction_date"])

    # Clean text fields (fixes trailing spaces e.g. 'Groceries ')
    text_cols = [
        "transaction_type",
        "transaction_description",
        "category",
        "location_city",
        "location_country",
    ]
    for col in text_cols:
        df[col] = clean_text(df[col])

    # Fill missing transaction types.
    # EDA: all 61 null types are INTEREST (GROSS/NET) credits.
    interest_mask = (
        df["transaction_type"].isna()
        & df["transaction_description"].str.contains("INTEREST", case=False, na=False)
    )
    df.loc[interest_mask, "transaction_type"] = "INT"
    df["transaction_type"] = df["transaction_type"].fillna("Unknown")

    # Fill remaining categorical nulls
    df["category"] = df["category"].fillna("Unknown")
    df["location_city"] = df["location_city"].fillna("Unknown")
    df["location_country"] = df["location_country"].fillna("Unknown")

    # Normalize casing on label columns so Swansea/swansea become one value.
    # Leave transaction_type / description alone (bank codes & free-text narratives).
    for col in ["category", "location_city", "location_country"]:
        df[col] = standardize_label_case(df[col])

    # Correct known bad country labels
    df["location_country"] = df["location_country"].replace(COUNTRY_CORRECTIONS)

    # Debit/Credit are mutually exclusive (never both, never neither).
    # Missing amount means that side did not apply — treat as 0.
    df["debit_amount"] = df["debit_amount"].fillna(0.0)
    df["credit_amount"] = df["credit_amount"].fillna(0.0)

    # Derived analytics columns
    df["transaction_direction"] = "Debit"
    df.loc[df["credit_amount"] > 0, "transaction_direction"] = "Credit"
    df["amount"] = df["credit_amount"] - df["debit_amount"]
    df["abs_amount"] = df["amount"].abs()

    df["year"] = df["transaction_date"].dt.year
    df["month"] = df["transaction_date"].dt.month
    df["year_month"] = df["transaction_date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["transaction_date"].dt.day_name()

    # Safety: drop exact duplicate rows (EDA found 0, keep for pipeline robustness)
    before_dedup = len(df)
    df = df.drop_duplicates()
    dropped = before_dedup - len(df)
    if dropped:
        print(f"Dropped {dropped} duplicate rows")

    # Chronological order for balance / time-series analysis
    df = df.sort_values(
        ["transaction_date", "transaction_number"],
        ascending=[True, True],
    ).reset_index(drop=True)

    # Final column order
    df = df[
        [
            "transaction_number",
            "transaction_date",
            "transaction_type",
            "transaction_description",
            "transaction_direction",
            "debit_amount",
            "credit_amount",
            "amount",
            "abs_amount",
            "balance",
            "category",
            "location_city",
            "location_country",
            "year",
            "month",
            "year_month",
            "day_of_week",
        ]
    ]

    return df


def save_processed(df: pd.DataFrame, output_dir: Path) -> Path:
    """Write cleaned data to data/processed."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "bank_transactions_cleaned.csv"
    df.to_csv(output_path, index=False)
    return output_path


# -----------------------------
# Run transform
# -----------------------------
if __name__ == "__main__":
    raw_df = extract()
    cleaned_df = transform(raw_df)

    print(f"Cleaned shape: {cleaned_df.shape}")
    print(
        f"Date range: {cleaned_df['transaction_date'].min().date()} -> "
        f"{cleaned_df['transaction_date'].max().date()}"
    )
    print("\nMissing values after transform:")
    print(cleaned_df.isnull().sum())
    print("\nPreview:")
    print(cleaned_df.head())

    output_file = save_processed(cleaned_df, PROCESSED_DATA_DIR)
    print(f"\nSaved cleaned dataset to: {output_file.resolve()}")
