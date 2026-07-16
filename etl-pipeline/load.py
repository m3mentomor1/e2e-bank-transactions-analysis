from pathlib import Path
import os
import sys
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Allow `python etl-pipeline/load.py` from the project root
ETL_DIR = Path(__file__).resolve().parent
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

from extract import PROJECT_ROOT

# -----------------------------
# Configuration
# -----------------------------
load_dotenv(PROJECT_ROOT / ".env")

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_FILE = PROCESSED_DATA_DIR / "bank_transactions_cleaned.csv"
TABLE_NAME = "bank_transactions"
CHUNK_SIZE = 500


def get_database_url() -> str | None:
    """
    Resolve a PostgreSQL connection URL for Supabase.

    Supported env vars (first match wins):
      - DATABASE_URL
      - SUPABASE_DB_URL
      - SUPABASE_URL + SUPABASE_DB_PASSWORD (or DB_PASSWORD)
    """
    direct_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if direct_url:
        return direct_url

    password = os.getenv("SUPABASE_DB_PASSWORD") or os.getenv("DB_PASSWORD")
    supabase_url = os.getenv("SUPABASE_URL", "")

    if password and supabase_url:
        project_ref = supabase_url.replace("https://", "").split(".")[0]
        host = os.getenv("DB_HOST", f"db.{project_ref}.supabase.co")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER", "postgres")
        dbname = os.getenv("DB_NAME", "postgres")
        encoded_password = quote_plus(password)
        return (
            f"postgresql+psycopg2://{user}:{encoded_password}@"
            f"{host}:{port}/{dbname}"
        )

    return None


def get_supabase_api_credentials() -> tuple[str, str] | None:
    """Return Supabase REST API credentials if configured."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if url and key:
        return url, key

    return None


def load_processed_data(path: Path = PROCESSED_FILE) -> pd.DataFrame:
    """Load cleaned CSV produced by transform.py."""
    if not path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {path}\n"
            "Run: python etl-pipeline/transform.py"
        )

    df = pd.read_csv(path, parse_dates=["transaction_date"])

    int_cols = ["transaction_number", "year", "month"]
    for col in int_cols:
        df[col] = df[col].astype(int)

    return df


def prepare_records(df: pd.DataFrame) -> list[dict]:
    """Convert dataframe rows to JSON-safe records for Supabase."""
    records = df.copy()
    records["transaction_date"] = records["transaction_date"].dt.strftime("%Y-%m-%d")
    return records.to_dict(orient="records")


def load_via_postgres(df: pd.DataFrame, *, truncate: bool = True) -> int:
    """Load data using a direct PostgreSQL connection."""
    database_url = get_database_url()
    if not database_url:
        raise ValueError("PostgreSQL connection URL is not configured.")

    engine = create_engine(database_url)

    if truncate:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME}"))

    rows_loaded = df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=CHUNK_SIZE,
    )

    return rows_loaded if rows_loaded is not None else len(df)


def load_via_supabase(df: pd.DataFrame) -> int:
    """Load data through the Supabase REST API."""
    from supabase import create_client

    credentials = get_supabase_api_credentials()
    if not credentials:
        raise ValueError("Supabase API credentials are not configured.")

    url, key = credentials
    client = create_client(url, key)
    records = prepare_records(df)

    total = 0
    for start in range(0, len(records), CHUNK_SIZE):
        batch = records[start : start + CHUNK_SIZE]
        client.table(TABLE_NAME).upsert(
            batch,
            on_conflict="transaction_number",
        ).execute()
        total += len(batch)

    return total


def load(df: pd.DataFrame, *, truncate: bool = True) -> int:
    """Load processed data into Supabase."""
    if get_database_url():
        print("Using PostgreSQL connection (SQLAlchemy)")
        return load_via_postgres(df, truncate=truncate)

    if get_supabase_api_credentials():
        print("Using Supabase REST API")
        return load_via_supabase(df)

    raise ValueError(
        "No database credentials found in .env.\n"
        "Add one of the following:\n"
        "  - DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres\n"
        "  - SUPABASE_DB_PASSWORD=[PASSWORD] (uses SUPABASE_URL to build the host)\n"
        "  - SUPABASE_URL + SUPABASE_KEY (REST API fallback)\n\n"
        "PostgreSQL connection string: Supabase → Project Settings → Database."
    )


# -----------------------------
# Run load
# -----------------------------
if __name__ == "__main__":
    df = load_processed_data()

    print(f"Loaded processed file: {PROCESSED_FILE.name}")
    print(f"Rows to insert: {len(df):,}")

    count = load(df)
    print(f"Loaded {count:,} rows into {TABLE_NAME}")
