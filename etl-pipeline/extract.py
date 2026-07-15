import os
import pandas as pd

# ---- CONFIG: update these to match your chosen Kaggle dataset ----
DATASET_PATH = "ank1r0/bank-transactions-dataset"
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
RAW_FILENAME = "laramee26openBankTransactionData.xlsx"  # update to match the actual file inside the dataset


def download_from_kaggle(dataset: str = DATASET_PATH, path: str = RAW_DATA_DIR) -> None:
    """
    Downloads and unzips the dataset from Kaggle into the raw data directory.
    Requires a valid ~/.kaggle/kaggle.json credentials file.
    Skips download if the target file already exists locally.
    """
    target_file = os.path.join(path, RAW_FILENAME)
    if os.path.exists(target_file):
        print(f"Raw file already exists at {target_file}, skipping download.")
        return

    import kaggle  # imported here so the script doesn't hard-fail if kaggle isn't installed/configured

    os.makedirs(path, exist_ok=True)
    print(f"Downloading dataset '{dataset}' from Kaggle...")
    kaggle.api.dataset_download_files(dataset, path=path, unzip=True)
    print(f"Download complete. Files saved to {path}")


def read_raw_file(raw_path: str) -> pd.DataFrame:
    """
    Reads the raw data file into a DataFrame, auto-detecting format
    (.csv or .xlsx) based on the file extension.
    """
    ext = os.path.splitext(raw_path)[1].lower()

    if ext == ".csv":
        return pd.read_csv(raw_path)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(raw_path)  # requires openpyxl installed
    else:
        raise ValueError(f"Unsupported file extension '{ext}' for {raw_path}")


def extract_data(use_kaggle_api: bool = True) -> pd.DataFrame:
    """
    Extracts the raw bank transactions data and returns it as a DataFrame.

    Args:
        use_kaggle_api: If True, attempts to download via the Kaggle API first.
                         If False, expects the file to already exist locally.

    Returns:
        pd.DataFrame: the raw, unprocessed transactions data.
    """
    raw_path = os.path.join(RAW_DATA_DIR, RAW_FILENAME)

    if use_kaggle_api:
        try:
            download_from_kaggle()
        except Exception as e:
            print(f"Kaggle API download failed ({e}). Falling back to local file at {raw_path}.")

    if not os.path.exists(raw_path):
        raise FileNotFoundError(
            f"Raw data file not found at {raw_path}. "
            f"Either place the file there manually or configure the Kaggle API."
        )

    print(f"Loading raw data from {raw_path}...")
    df = read_raw_file(raw_path)
    print(f"Extracted {len(df)} rows, {len(df.columns)} columns.")

    return df


if __name__ == "__main__":
    # Allows running this file standalone to test extraction in isolation
    df = extract_data()
    print(df.head())
    print(df.info())