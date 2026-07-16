"""Entry point for `python etl-pipeline`."""

import sys
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

from main import run_pipeline

if __name__ == "__main__":
    run_pipeline()
