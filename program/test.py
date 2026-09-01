"""
Automated test suite for the Bank Transaction Fraud Detection System.

Runs without manual input. Each test prints feature, input, expected,
actual, and PASS/FAIL outcome.
"""

import csv
import io
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from config_loader import load_config
from file_handler import read_transaction_file
from fraud_detector import (
    detect_high_value,
    detect_multiple_locations,
    detect_repeated_declined,
    detect_time_based_declined,
    run_all_detections,
)
from main import process_transactions
from reporter import export_summary_csv, generate_summary
from storage import TransactionStore
from validator import export_invalid_records, validate_all_lines, validate_record

os.chdir(Path(__file__).resolve().parent)


def print_test_result(feature, test_input, expected, actual, passed):
    """Print a formatted test result line."""
    status = "PASS" if passed else "FAIL"
    print(f"\nFeature: {feature}")
    print(f"Input: {test_input}")
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    print(f"Outcome: {status}")
    return passed


class TestFileHandler(unittest.TestCase):
    """Tests for reading transaction files."""

    def test_read_valid_file(self):
        lines, error = read_transaction_file("transactions.txt")
        passed = error is None and len(lines) > 0
        print_test_result(
            "Read valid transaction file",
            "transactions.txt",
            "Lines returned, no error",
            f"{len(lines)} lines, error={error}",
            passed,
        )
        self.assertIsNone(error)
        self.assertGreater(len(lines), 0)

    def test_missing_file(self):
        lines, error = read_transaction_file("nonexistent_file.txt")
        passed = error is not None and len(lines) == 0
        print_test_result(
            "Handle missing file",
            "nonexistent_file.txt",
            "Error message, empty lines",
            f"error='{error}', lines={len(lines)}",
            passed,
        )
        self.assertIsNotNone(error)
        self.assertEqual(lines, [])

    def test_empty_file(self):
        lines, error = read_transaction_file("transactions_empty.txt")
        passed = error is not None
        print_test_result(
            "Handle empty file",
            "transactions_empty.txt",
            "Error message",
            f"error='{error}'",
            passed,
        )
        self.assertIsNotNone(error)


class TestValidator(unittest.TestCase):
    """Tests for transaction validation."""

    def setUp(self):
        self.seen_ids = set()
        self.seen_keys = set()

    def test_wrong_field_count(self):
        line = "2026-07-11 09:15:23 | T1001 | A10025 | TRANSFER | 100.00"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = txn is None and invalid is not None
        print_test_result(
            "Reject incorrect field count",
            line,
            "Invalid record returned",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNone(txn)
        self.assertIn("Incorrect number of fields", invalid["reason"])

    def test_invalid_transaction_type(self):
        line = "2026-07-11 09:15:23 | T2001 | A10025 | INVALID_TYPE | 100.00 | Brisbane | APPROVED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "Invalid transaction type" in invalid["reason"]
        print_test_result(
            "Reject invalid transaction type",
            "INVALID_TYPE",
            "Invalid transaction type error",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_invalid_status(self):
        line = "2026-07-11 09:15:23 | T2002 | A10025 | TRANSFER | 100.00 | Brisbane | REJECTED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "Invalid status" in invalid["reason"]
        print_test_result(
            "Reject invalid status value",
            "REJECTED",
            "Invalid status error",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_non_numeric_amount(self):
        line = "2026-07-11 09:15:23 | T2003 | A10025 | TRANSFER | abc | Brisbane | APPROVED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "not numeric" in invalid["reason"]
        print_test_result(
            "Reject non-numeric amount",
            "abc",
            "Amount is not numeric",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_zero_amount(self):
        line = "2026-07-11 09:15:23 | T2004 | A10025 | TRANSFER | 0.00 | Brisbane | APPROVED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "greater than zero" in invalid["reason"]
        print_test_result(
            "Reject zero amount",
            "0.00",
            "Amount must be greater than zero",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_negative_amount(self):
        line = "2026-07-11 09:15:23 | T2005 | A10025 | TRANSFER | -100.00 | Brisbane | APPROVED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "greater than zero" in invalid["reason"]
        print_test_result(
            "Reject negative amount",
            "-100.00",
            "Amount must be greater than zero",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_invalid_timestamp(self):
        line = "2026/07/11 09:15:23 | T2006 | A10025 | TRANSFER | 100.00 | Brisbane | APPROVED"
        txn, invalid = validate_record(line, 1, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "timestamp" in invalid["field"]
        print_test_result(
            "Reject invalid timestamp format",
            "2026/07/11 09:15:23",
            "Invalid timestamp error",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)

    def test_duplicate_transaction_id(self):
        line1 = "2026-07-11 09:15:23 | T3001 | A10025 | TRANSFER | 100.00 | Brisbane | APPROVED"
        line2 = "2026-07-11 10:15:23 | T3001 | A10025 | TRANSFER | 200.00 | Sydney | APPROVED"
        validate_record(line1, 1, self.seen_ids, self.seen_keys)
        txn, invalid = validate_record(line2, 2, self.seen_ids, self.seen_keys)
        passed = invalid is not None and "Duplicate transaction ID" in invalid["reason"]
        print_test_result(
            "Reject duplicate transaction ID",
            "T3001 twice",
            "Duplicate transaction ID error",
            invalid["reason"] if invalid else "None",
            passed,
        )
        self.assertIsNotNone(invalid)


class TestFraudDetection(unittest.TestCase):
    """Tests for fraud detection rules."""

    def setUp(self):
        self.config = load_config("config.json")

    def _make_txn(self, txn_id, account_id, amount, status, location, timestamp_str):
        return {
            "transaction_id": txn_id,
            "account_id": account_id,
            "amount": amount,
            "status": status,
            "location": location,
            "timestamp": datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
            "transaction_type": "TRANSFER",
            "line_number": 1,
        }

    def test_high_value_detection(self):
        txns = [self._make_txn("T9001", "A10025", 6500.00, "APPROVED", "Brisbane", "2026-07-11 09:00:00")]
        alerts = detect_high_value(txns, self.config)
        passed = len(alerts) == 1 and alerts[0]["transaction_id"] == "T9001"
        print_test_result(
            "Detect high-value approved transaction",
            "T9001, $6500 APPROVED",
            "1 alert for T9001",
            f"{len(alerts)} alert(s)",
            passed,
        )
        self.assertEqual(len(alerts), 1)

    def test_repeated_declined_detection(self):
        by_account = {
            "A55555": [
                self._make_txn(f"T9{i:03d}", "A55555", 50, "DECLINED", "Sydney", f"2026-07-11 {10+i}:00:00")
                for i in range(5)
            ]
        }
        alerts = detect_repeated_declined(by_account, self.config)
        passed = len(alerts) == 1 and alerts[0]["account_id"] == "A55555"
        print_test_result(
            "Detect repeated declined transactions",
            "A55555 with 5 declined",
            "1 alert for A55555",
            f"{len(alerts)} alert(s) for {alerts[0]['account_id'] if alerts else 'none'}",
            passed,
        )
        self.assertEqual(len(alerts), 1)

    def test_multiple_locations_detection(self):
        locations = ["Brisbane", "Sydney", "Gold Coast", "Melbourne"]
        by_account = {
            "A77777": [
                self._make_txn(f"T8{i:03d}", "A77777", 100, "APPROVED", loc, "2026-07-11 12:00:00")
                for i, loc in enumerate(locations)
            ]
        }
        alerts = detect_multiple_locations(by_account, self.config)
        passed = len(alerts) == 1 and alerts[0]["location_count"] == 4
        print_test_result(
            "Detect multiple locations",
            "A77777 in 4 locations",
            "1 alert, 4 locations",
            f"{len(alerts)} alert(s), {alerts[0]['location_count'] if alerts else 0} locations",
            passed,
        )
        self.assertEqual(len(alerts), 1)

    def test_time_based_declined_suspicious(self):
        by_account = {
            "A33333": [
                self._make_txn(
                    f"T7{i:03d}", "A33333", 30, "DECLINED", "Brisbane",
                    f"2026-07-11 14:{i*5:02d}:00"
                )
                for i in range(4)
            ]
        }
        alerts = detect_time_based_declined(by_account, self.config)
        passed = len(alerts) == 1
        print_test_result(
            "Detect time-based declined burst (suspicious)",
            "4 declined within 20 minutes",
            "1 alert",
            f"{len(alerts)} alert(s)",
            passed,
        )
        self.assertEqual(len(alerts), 1)

    def test_time_based_declined_normal(self):
        by_account = {
            "A99999": [
                self._make_txn("T6001", "A99999", 30, "DECLINED", "Brisbane", "2026-07-11 08:00:00"),
                self._make_txn("T6002", "A99999", 30, "DECLINED", "Brisbane", "2026-07-11 12:00:00"),
            ]
        }
        alerts = detect_time_based_declined(by_account, self.config)
        passed = len(alerts) == 0
        print_test_result(
            "Time-based rule - normal account",
            "2 declined, 4 hours apart",
            "0 alerts",
            f"{len(alerts)} alert(s)",
            passed,
        )
        self.assertEqual(len(alerts), 0)

    def test_normal_account_not_flagged(self):
        by_account = {
            "A99999": [
                self._make_txn("T5001", "A99999", 200, "APPROVED", "Brisbane", "2026-07-11 10:00:00"),
                self._make_txn("T5002", "A99999", 45, "APPROVED", "Brisbane", "2026-07-11 10:05:00"),
            ]
        }
        txns = by_account["A99999"]
        alerts = run_all_detections(txns, by_account, self.config)
        account_alerts = [a for a in alerts if a.get("account_id") == "A99999"]
        passed = len(account_alerts) == 0
        print_test_result(
            "Normal account not incorrectly flagged",
            "A99999, small approved txns, 1 location",
            "0 alerts for A99999",
            f"{len(account_alerts)} alert(s)",
            passed,
        )
        self.assertEqual(len(account_alerts), 0)


class TestConfigAndReporting(unittest.TestCase):
    """Tests for configuration loading and reporting."""

    def test_config_loading(self):
        config = load_config("config.json")
        passed = (
            config["high_value_threshold"] == 5000
            and config["declined_count_threshold"] == 4
            and config["location_count_threshold"] == 3
        )
        print_test_result(
            "Load configuration from JSON",
            "config.json",
            "Thresholds loaded correctly",
            f"high_value={config['high_value_threshold']}, declined={config['declined_count_threshold']}",
            passed,
        )
        self.assertEqual(config["high_value_threshold"], 5000)

    def test_summary_statistics(self):
        txns = [
            {
                "transaction_id": "T1", "account_id": "A1", "amount": 100,
                "status": "APPROVED", "location": "Brisbane",
            },
            {
                "transaction_id": "T2", "account_id": "A2", "amount": 6000,
                "status": "APPROVED", "location": "Sydney",
            },
        ]
        invalid = [{"line_number": 3, "field": "amount", "value": "abc", "reason": "not numeric"}]
        alerts = [{"rule": "High-Value Transactions", "alert_type": "transaction",
                   "transaction_id": "T2", "account_id": "A2"}]
        summary = generate_summary(txns, invalid, alerts)
        passed = (
            summary["total_records_processed"] == 3
            and summary["total_valid_records"] == 2
            and summary["total_invalid_records"] == 1
            and summary["high_value_alerts"] == 1
        )
        print_test_result(
            "Generate summary statistics",
            "2 valid, 1 invalid, 1 alert",
            "Correct counts",
            f"processed={summary['total_records_processed']}, valid={summary['total_valid_records']}",
            passed,
        )
        self.assertEqual(summary["total_valid_records"], 2)

    def test_invalid_export_csv(self):
        invalid = [
            {"line_number": 1, "field": "amount", "value": "abc", "reason": "not numeric"},
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = export_invalid_records(invalid, tmp_path)
            with open(tmp_path, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            passed = result and len(rows) == 1
            print_test_result(
                "Export invalid records to CSV",
                "1 invalid record",
                "CSV with 1 row",
                f"result={result}, rows={len(rows)}",
                passed,
            )
            self.assertTrue(result)
        finally:
            os.unlink(tmp_path)

    def test_summary_csv_export(self):
        summary = {"total_valid_records": 10, "total_invalid_records": 2}
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = export_summary_csv(summary, tmp_path)
            with open(tmp_path, encoding="utf-8") as f:
                rows = list(csv.reader(f))
            passed = result and len(rows) >= 3
            print_test_result(
                "Export summary to CSV",
                "summary dict",
                "CSV file created",
                f"result={result}, rows={len(rows)}",
                passed,
            )
            self.assertTrue(result)
        finally:
            os.unlink(tmp_path)


class TestFullPipeline(unittest.TestCase):
    """Integration test for the complete pipeline."""

    def test_full_pipeline_with_sample_data(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            store, alerts, summary = process_transactions("transactions.txt", "config.json")

        passed = store is not None and summary is not None and summary["total_valid_records"] > 0
        print_test_result(
            "Full pipeline with sample data",
            "transactions.txt",
            "Valid records processed, summary generated",
            f"valid={summary['total_valid_records'] if summary else 0}, alerts={len(alerts)}",
            passed,
        )
        self.assertIsNotNone(store)
        self.assertGreater(summary["total_valid_records"], 0)


def run_tests():
    """Run all tests and print a summary."""
    print("=" * 70)
    print("BANK TRANSACTION FRAUD DETECTION - TEST SUITE")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestFileHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestFraudDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigAndReporting))
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipeline))

    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w"))
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.splitlines()[-1]}")

    if result.errors:
        print("\nErrors:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace.splitlines()[-1]}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
