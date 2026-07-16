"""
Run the complete ETL pipeline: extract → transform → load.

Usage:
    python etl-pipeline
"""

from dotenv import load_dotenv

from extract import PROJECT_ROOT, extract
from load import TABLE_NAME, load
from transform import PROCESSED_DATA_DIR, save_processed, transform

load_dotenv(PROJECT_ROOT / ".env")


def run_pipeline() -> None:
    print("=" * 60)
    print("STEP 1: Extract")
    print("=" * 60)
    raw_df = extract()

    print("\n" + "=" * 60)
    print("STEP 2: Transform")
    print("=" * 60)
    cleaned_df = transform(raw_df)
    output_file = save_processed(cleaned_df, PROCESSED_DATA_DIR)

    print(f"Cleaned shape: {cleaned_df.shape}")
    print(
        f"Date range: {cleaned_df['transaction_date'].min().date()} -> "
        f"{cleaned_df['transaction_date'].max().date()}"
    )
    print(f"Saved processed file: {output_file.resolve()}")

    print("\n" + "=" * 60)
    print("STEP 3: Load")
    print("=" * 60)
    rows_loaded = load(cleaned_df)
    print(f"Loaded {rows_loaded:,} rows into {TABLE_NAME}")

    print("\n" + "=" * 60)
    print("ETL pipeline completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
