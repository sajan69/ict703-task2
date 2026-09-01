"""
Bank Transaction Fraud Detection System - Main Entry Point

Reads transaction files, validates records, detects suspicious activity,
and generates summary reports.
"""

import os
from pathlib import Path

from config_loader import load_config
from file_handler import read_transaction_file
from fraud_detector import run_all_detections
from reporter import display_alerts, export_summary_csv, generate_summary, print_summary
from storage import TransactionStore
from validator import export_invalid_records, validate_all_lines


def process_transactions(transaction_file="transactions.txt", config_file="config.json"):
    """
    Run the full fraud detection pipeline.

    Args:
        transaction_file: Path to the transaction data file.
        config_file: Path to the JSON configuration file.

    Returns:
        A tuple of (store, alerts, summary) or (None, [], None) on file error.
    """
    print("Bank Transaction Fraud Detection System")
    print("-" * 40)

    config = load_config(config_file)
    lines, error = read_transaction_file(transaction_file)

    if error:
        print(error)
        return None, [], None

    print(f"Reading transactions from '{transaction_file}'...")
    valid_transactions, invalid_records = validate_all_lines(lines)

    store = TransactionStore()
    store.load_valid_transactions(valid_transactions)
    store.invalid_records = invalid_records

    print(f"\nValidation complete: {len(valid_transactions)} valid, "
          f"{len(invalid_records)} invalid record(s).")

    if invalid_records:
        export_invalid_records(invalid_records)

    alerts = run_all_detections(store.transactions, store.by_account, config)
    display_alerts(alerts)

    summary = generate_summary(store.transactions, invalid_records, alerts)
    print_summary(summary)
    export_summary_csv(summary)

    return store, alerts, summary


def main():
    """Main program entry point."""
    os.chdir(Path(__file__).resolve().parent)
    process_transactions()


if __name__ == "__main__":
    main()
