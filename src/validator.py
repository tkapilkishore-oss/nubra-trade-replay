"""
Data validation engine for Nubra Trade Replay.
Enforces the data contract specified in data_spec.md.
"""

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Union
import pandas as pd

from src.models import REQUIRED_COLUMNS, ValidationResult


def parse_and_validate_csv(
    source: Union[str, Path, StringIO, bytes],
) -> ValidationResult:
    """
    Load and rigorously validate a CSV source against data_spec.md rules.
    Does not drop rows or alter values silently.
    Returns a ValidationResult object with detailed errors, warnings, and normalized df.
    """
    errors = []
    warnings = []

    # Read CSV
    try:
        if isinstance(source, (str, Path)) and Path(str(source)).exists():
            df = pd.read_csv(source)
        elif isinstance(source, bytes):
            df = pd.read_csv(StringIO(source.decode("utf-8", errors="replace")))
        elif isinstance(source, StringIO):
            df = pd.read_csv(source)
        else:
            return ValidationResult(
                is_valid=False,
                errors=["Unable to read file: invalid input source or file not found."],
            )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"CSV parsing error: {str(e)}. Please check that the file is valid UTF-8 formatted CSV."],
        )

    # 1. Empty dataset check
    row_count = len(df)
    if row_count == 0:
        return ValidationResult(
            is_valid=False,
            errors=["The uploaded dataset contains 0 completed trades. Please provide a file with trade data."],
            row_count=0,
        )

    # 2. Required columns check
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}.")

    extra_cols = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if extra_cols:
        warnings.append(f"Ignoring extra columns not in specification: {', '.join(extra_cols)}.")

    if errors:
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            row_count=row_count,
        )

    # Work on a copy of required columns
    validated_df = df[REQUIRED_COLUMNS].copy()

    # 3. Missing/NaN values check
    null_counts = validated_df.isna().sum()
    cols_with_nulls = null_counts[null_counts > 0].to_dict()
    if cols_with_nulls:
        null_details = [f"{col} ({cnt} missing)" for col, cnt in cols_with_nulls.items()]
        errors.append(f"Dataset contains missing values in columns: {', '.join(null_details)}.")

    # 4. trade_id uniqueness
    # Check for empty or non-string IDs
    non_str_ids = validated_df[validated_df["trade_id"].isna() | (validated_df["trade_id"].astype(str).str.strip() == "")]
    if not non_str_ids.empty:
        errors.append(f"Found {len(non_str_ids)} rows with empty or missing trade_id.")

    if validated_df["trade_id"].duplicated().any():
        dups = validated_df[validated_df["trade_id"].duplicated(keep=False)]["trade_id"].unique().tolist()
        errors.append(f"Duplicate trade_id values found: {dups[:5]} (each trade_id must be unique).")

    # 5. Date validation (YYYY-MM-DD)
    date_errors = []
    for idx, val in validated_df["date"].items():
        try:
            d_str = str(val).strip()
            parsed_d = datetime.strptime(d_str, "%Y-%m-%d").date()
        except ValueError:
            date_errors.append(f"Row {idx + 1}: '{val}' is not valid YYYY-MM-DD format")
    if date_errors:
        errors.append(f"Invalid trading dates found: {'; '.join(date_errors[:4])}{'...' if len(date_errors) > 4 else ''}.")

    # 6. Time validation & same-day entry < exit integrity
    time_format_errors = []
    order_errors = []
    for idx, row in validated_df.iterrows():
        try:
            t_entry = datetime.strptime(str(row["entry_time"]).strip(), "%H:%M:%S").time()
        except ValueError:
            time_format_errors.append(f"Row {idx + 1}: invalid entry_time '{row['entry_time']}'")
            continue

        try:
            t_exit = datetime.strptime(str(row["exit_time"]).strip(), "%H:%M:%S").time()
        except ValueError:
            time_format_errors.append(f"Row {idx + 1}: invalid exit_time '{row['exit_time']}'")
            continue

        if t_entry >= t_exit:
            order_errors.append(
                f"Trade '{row['trade_id']}': entry_time ({t_entry}) occurs on or after exit_time ({t_exit})"
            )

    if time_format_errors:
        errors.append(f"Invalid time format (expected 24-hr HH:MM:SS): {'; '.join(time_format_errors[:4])}.")
    if order_errors:
        errors.append(f"Entry times must precede exit times on same-day trades: {'; '.join(order_errors[:4])}.")

    # 7. Quantity check (positive integer)
    try:
        qty_numeric = pd.to_numeric(validated_df["quantity"], errors="coerce")
        if qty_numeric.isna().any():
            errors.append("Column 'quantity' contains non-numeric values.")
        else:
            if (qty_numeric <= 0).any():
                invalid_qty_ids = validated_df[qty_numeric <= 0]["trade_id"].tolist()
                errors.append(f"Quantities must be strictly positive (> 0). Invalid trade IDs: {invalid_qty_ids[:4]}.")
            if (qty_numeric % 1 != 0).any():
                errors.append("Quantities must be whole integers (contracts / units).")
            validated_df["quantity"] = qty_numeric.astype(int)
    except Exception as e:
        errors.append(f"Error parsing quantity: {str(e)}")

    # 8. Price checks (strictly positive)
    for price_col in ["entry_price", "exit_price"]:
        try:
            price_num = pd.to_numeric(validated_df[price_col], errors="coerce")
            if price_num.isna().any():
                errors.append(f"Column '{price_col}' contains non-numeric values.")
            else:
                if (price_num <= 0).any():
                    bad_ids = validated_df[price_num <= 0]["trade_id"].tolist()
                    errors.append(f"Prices in '{price_col}' must be strictly positive (> 0). Invalid trades: {bad_ids[:4]}.")
                validated_df[price_col] = price_num.astype(float)
        except Exception as e:
            errors.append(f"Error parsing {price_col}: {str(e)}")

    # 9. Charges check (non-negative)
    try:
        charges_num = pd.to_numeric(validated_df["charges"], errors="coerce")
        if charges_num.isna().any():
            errors.append("Column 'charges' contains non-numeric values.")
        else:
            if (charges_num < 0).any():
                neg_charge_ids = validated_df[charges_num < 0]["trade_id"].tolist()
                errors.append(f"Charges cannot be negative (>= 0). Invalid trades: {neg_charge_ids[:4]}.")
            validated_df["charges"] = charges_num.astype(float)
    except Exception as e:
        errors.append(f"Error parsing charges: {str(e)}")

    # 10. is_expiry_day boolean check
    try:
        raw_expiry = validated_df["is_expiry_day"]
        # Normalize various representations (True, False, 1, 0, 'true', 'TRUE', 'false', 'FALSE')
        valid_bool_map = {
            True: True,
            False: False,
            1: True,
            0: False,
            "true": True,
            "false": False,
            "True": True,
            "False": False,
            "TRUE": True,
            "FALSE": False,
            "1": True,
            "0": False,
        }
        unrecognized = []
        parsed_expiry = []
        for idx, val in raw_expiry.items():
            if val in valid_bool_map:
                parsed_expiry.append(valid_bool_map[val])
            elif str(val).strip().lower() in ["true", "1", "yes"]:
                parsed_expiry.append(True)
            elif str(val).strip().lower() in ["false", "0", "no"]:
                parsed_expiry.append(False)
            else:
                unrecognized.append((idx + 1, val))

        if unrecognized:
            errors.append(
                f"Column 'is_expiry_day' contains non-boolean values in row(s): {unrecognized[:4]} (expected True or False)."
            )
        else:
            validated_df["is_expiry_day"] = parsed_expiry
    except Exception as e:
        errors.append(f"Error parsing is_expiry_day: {str(e)}")

    is_valid = len(errors) == 0

    if is_valid:
        # Standardize strings
        validated_df["trade_id"] = validated_df["trade_id"].astype(str).str.strip()
        validated_df["date"] = validated_df["date"].astype(str).str.strip()
        validated_df["entry_time"] = validated_df["entry_time"].astype(str).str.strip()
        validated_df["exit_time"] = validated_df["exit_time"].astype(str).str.strip()
        validated_df["symbol"] = validated_df["symbol"].astype(str).str.strip()

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        row_count=row_count,
        df=validated_df if is_valid else None,
    )
