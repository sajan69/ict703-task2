"""
Transaction validation module with core and enhanced validation checks.
"""

import csv
import re
from datetime import datetime

VALID_TRANSACTION_TYPES = {
    "TRANSFER",
    "CARD_PAYMENT",
    "CASH_WITHDRAWAL",
    "ONLINE_PURCHASE",
    "DIRECT_DEBIT",
}

VALID_STATUSES = {"APPROVED", "DECLINED", "PENDING"}

TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TRANSACTION_ID_PATTERN = re.compile(r"^T\d{4}$")
ACCOUNT_ID_PATTERN = re.compile(r"^A\d{5}$")
AMOUNT_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")


def _make_invalid(line_number, field, value, reason):
    """Create a standard invalid record dictionary."""
    return {
        "line_number": line_number,
        "field": field,
        "value": value,
        "reason": reason,
    }


def validate_record(line, line_number, seen_transaction_ids, seen_record_keys):
    """
    Validate a single transaction record line.

    Args:
        line: Raw line from the transaction file.
        line_number: 1-based line number for error reporting.
        seen_transaction_ids: Set of transaction IDs already accepted.
        seen_record_keys: Set of normalized record keys for duplicate detection.

    Returns:
        A tuple of (transaction_dict_or_none, invalid_record_or_none).
    """
    stripped = line.strip()
    if not stripped:
        return None, None

    parts = [part.strip() for part in stripped.split("|")]

    if len(parts) != 7:
        return None, _make_invalid(
            line_number,
            "record",
            stripped,
            f"Incorrect number of fields (expected 7, found {len(parts)})",
        )

    timestamp_str, transaction_id, account_id, transaction_type, amount_str, location, status = parts

    if not transaction_id:
        return None, _make_invalid(line_number, "transaction_id", transaction_id, "Transaction ID is empty")

    if not account_id:
        return None, _make_invalid(line_number, "account_id", account_id, "Account ID is empty")

    if not TIMESTAMP_PATTERN.match(timestamp_str):
        return None, _make_invalid(
            line_number,
            "timestamp",
            timestamp_str,
            "Invalid timestamp format (expected YYYY-MM-DD HH:MM:SS)",
        )

    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None, _make_invalid(
            line_number,
            "timestamp",
            timestamp_str,
            "Invalid timestamp value",
        )

    if not TRANSACTION_ID_PATTERN.match(transaction_id):
        return None, _make_invalid(
            line_number,
            "transaction_id",
            transaction_id,
            "Invalid transaction ID format (expected T followed by 4 digits)",
        )

    if not ACCOUNT_ID_PATTERN.match(account_id):
        return None, _make_invalid(
            line_number,
            "account_id",
            account_id,
            "Invalid account ID format (expected A followed by 5 digits)",
        )

    if transaction_type not in VALID_TRANSACTION_TYPES:
        return None, _make_invalid(
            line_number,
            "transaction_type",
            transaction_type,
            f"Invalid transaction type '{transaction_type}'",
        )

    if status not in VALID_STATUSES:
        return None, _make_invalid(
            line_number,
            "status",
            status,
            f"Invalid status value '{status}'",
        )

    if not location:
        return None, _make_invalid(line_number, "location", location, "Location is empty")

    try:
        amount = float(amount_str)
    except ValueError:
        return None, _make_invalid(
            line_number,
            "amount",
            amount_str,
            "Amount is not numeric",
        )

    if amount <= 0:
        return None, _make_invalid(
            line_number,
            "amount",
            amount_str,
            "Amount must be greater than zero",
        )

    if not AMOUNT_PATTERN.match(amount_str):
        return None, _make_invalid(
            line_number,
            "amount",
            amount_str,
            "Amount must have up to two decimal places",
        )

    if transaction_id in seen_transaction_ids:
        return None, _make_invalid(
            line_number,
            "transaction_id",
            transaction_id,
            f"Duplicate transaction ID '{transaction_id}'",
        )

    record_key = "|".join(
        [
            timestamp_str,
            transaction_id,
            account_id,
            transaction_type,
            f"{amount:.2f}",
            location,
            status,
        ]
    )
    if record_key in seen_record_keys:
        return None, _make_invalid(
            line_number,
            "record",
            stripped,
            "Duplicate transaction record",
        )

    seen_transaction_ids.add(transaction_id)
    seen_record_keys.add(record_key)

    transaction = {
        "timestamp": timestamp,
        "transaction_id": transaction_id,
        "account_id": account_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "location": location,
        "status": status,
        "line_number": line_number,
    }
    return transaction, None


def validate_all_lines(lines):
    """
    Validate all lines from a transaction file.

    Args:
        lines: List of raw lines including blank lines.

    Returns:
        A tuple of (valid_transactions, invalid_records).
    """
    valid_transactions = []
    invalid_records = []
    seen_transaction_ids = set()
    seen_record_keys = set()

    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        transaction, invalid = validate_record(
            line, index, seen_transaction_ids, seen_record_keys
        )

        if invalid:
            invalid_records.append(invalid)
            print(
                f"Line {invalid['line_number']}: Rejected - "
                f"{invalid['field']} '{invalid['value']}' - {invalid['reason']}"
            )
        elif transaction:
            valid_transactions.append(transaction)

    return valid_transactions, invalid_records


def export_invalid_records(invalid_records, filepath="invalid_export.csv"):
    """
    Export invalid records to a CSV file.

    Args:
        invalid_records: List of invalid record dictionaries.
        filepath: Output CSV file path.

    Returns:
        True if export succeeded, False otherwise.
    """
    if not invalid_records:
        return False

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["line_number", "field", "value", "reason"],
            )
            writer.writeheader()
            writer.writerows(invalid_records)
    except OSError as exc:
        print(f"Error: Unable to export invalid records - {exc}")
        return False

    print(f"Invalid records exported to '{filepath}'")
    return True
