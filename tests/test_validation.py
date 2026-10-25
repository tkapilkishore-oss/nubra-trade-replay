import sys
from io import StringIO
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.validator import parse_and_validate_csv

SAMPLE_VALID_HEADER = (
    "trade_id,date,entry_time,exit_time,symbol,quantity,entry_price,exit_price,charges,is_expiry_day\n"
)


def test_valid_csv():
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,50,100.0,110.0,20.0,False\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.row_count == 1
    assert res.df is not None


def test_empty_dataset():
    res = parse_and_validate_csv(StringIO(SAMPLE_VALID_HEADER))
    assert res.is_valid is False
    assert any("0 completed trades" in err for err in res.errors)


def test_missing_column():
    bad_header = "trade_id,date,entry_time,exit_time,symbol,quantity,entry_price,exit_price,charges\n"  # missing is_expiry_day
    csv_data = bad_header + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,50,100.0,110.0,20.0\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("Missing required columns" in err and "is_expiry_day" in err for err in res.errors)


def test_duplicate_trade_ids():
    csv_data = (
        SAMPLE_VALID_HEADER
        + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,50,100.0,110.0,20.0,False\n"
        + "T001,2026-09-01,10:00:00,10:15:00,NIFTY_CE,50,100.0,105.0,20.0,False\n"
    )
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("Duplicate trade_id" in err for err in res.errors)


def test_missing_null_values():
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,09:30:00,09:45:00,,50,100.0,110.0,20.0,False\n"  # missing symbol
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("missing values" in err for err in res.errors)


def test_invalid_date_format():
    csv_data = SAMPLE_VALID_HEADER + "T001,01/09/2026,09:30:00,09:45:00,NIFTY_CE,50,100.0,110.0,20.0,False\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("Invalid trading dates" in err for err in res.errors)


def test_entry_after_exit():
    # entry 10:00:00 is after exit 09:30:00
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,10:00:00,09:30:00,NIFTY_CE,50,100.0,110.0,20.0,False\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("entry times must precede exit times" in err.lower() for err in res.errors)


def test_negative_quantity():
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,-10,100.0,110.0,20.0,False\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("strictly positive" in err for err in res.errors)


def test_negative_charges():
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,10,100.0,110.0,-5.0,False\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("cannot be negative" in err for err in res.errors)


def test_non_boolean_expiry():
    csv_data = SAMPLE_VALID_HEADER + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,10,100.0,110.0,20.0,MAYBE\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is False
    assert any("non-boolean values" in err for err in res.errors)


def test_extra_columns_trigger_warning():
    extra_header = SAMPLE_VALID_HEADER.strip() + ",broker_notes\n"
    csv_data = extra_header + "T001,2026-09-01,09:30:00,09:45:00,NIFTY_CE,50,100.0,110.0,20.0,False,Some note\n"
    res = parse_and_validate_csv(StringIO(csv_data))
    assert res.is_valid is True
    assert len(res.warnings) == 1
    assert "broker_notes" in res.warnings[0]


if __name__ == "__main__":
    test_valid_csv()
    test_empty_dataset()
    test_missing_column()
    test_duplicate_trade_ids()
    test_missing_null_values()
    test_invalid_date_format()
    test_entry_after_exit()
    test_negative_quantity()
    test_negative_charges()
    test_non_boolean_expiry()
    test_extra_columns_trigger_warning()
    print("All validation tests passed successfully!")
