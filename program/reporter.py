"""
Reporting module for displaying alerts and generating summary statistics.
"""

import csv


def display_alerts(alerts):
    """
    Display fraud detection alerts to the console.

    Args:
        alerts: List of alert dictionaries from fraud detection rules.
    """
    print("\n" + "=" * 70)
    print("SUSPICIOUS ACTIVITY REPORT")
    print("=" * 70)

    if not alerts:
        print("\nNo suspicious activity detected.")
        return

    for index, alert in enumerate(alerts, start=1):
        print(f"\n--- Alert {index} ---")
        print(f"Rule: {alert['rule']} (Severity: {alert.get('severity', 'N/A')})")

        if alert.get("alert_type") == "transaction":
            print(f"Transaction ID: {alert['transaction_id']}")
            print(f"Account ID: {alert['account_id']}")
            print(f"Amount: ${alert['amount']:,.2f}")
        else:
            print(f"Account ID: {alert['account_id']}")
            if "declined_count" in alert:
                print(f"Declined Transactions: {alert['declined_count']}")
            if "location_count" in alert:
                print(f"Different Locations: {alert['location_count']}")
                print(f"Locations: {', '.join(alert['locations'])}")
            if "declined_in_window" in alert:
                print(
                    f"Declined in {alert['time_window_minutes']}-minute window: "
                    f"{alert['declined_in_window']}"
                )
            if alert.get("transaction_ids"):
                print(f"Relevant Transaction IDs: {', '.join(alert['transaction_ids'])}")

        print(f"Reason: {alert['reason']}")


def generate_summary(transactions, invalid_records, alerts):
    """
    Generate summary statistics for processed transactions and alerts.

    Args:
        transactions: List of valid transaction dictionaries.
        invalid_records: List of invalid record dictionaries.
        alerts: List of alert dictionaries.

    Returns:
        Dictionary of summary statistics.
    """
    total_processed = len(transactions) + len(invalid_records)
    approved = [txn for txn in transactions if txn["status"] == "APPROVED"]
    declined = [txn for txn in transactions if txn["status"] == "DECLINED"]

    suspicious_txn_ids = {
        alert["transaction_id"]
        for alert in alerts
        if alert.get("alert_type") == "transaction" and "transaction_id" in alert
    }
    suspicious_accounts = {
        alert["account_id"] for alert in alerts if alert.get("account_id")
    }

    rule_counts = {}
    for alert in alerts:
        rule = alert["rule"]
        rule_counts[rule] = rule_counts.get(rule, 0) + 1

    return {
        "total_records_processed": total_processed,
        "total_valid_records": len(transactions),
        "total_invalid_records": len(invalid_records),
        "total_approved_transactions": len(approved),
        "total_declined_transactions": len(declined),
        "total_approved_value": sum(txn["amount"] for txn in approved),
        "total_suspicious_transactions": len(suspicious_txn_ids),
        "total_suspicious_accounts": len(suspicious_accounts),
        "high_value_alerts": rule_counts.get("High-Value Transactions", 0),
        "repeated_decline_alerts": rule_counts.get("Repeated Declined Transactions", 0),
        "multiple_location_alerts": rule_counts.get("Multiple Locations", 0),
        "time_based_alerts": rule_counts.get("Time-Based Declined Burst", 0),
    }


def print_summary(summary):
    """Print summary statistics to the console."""
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total records processed:       {summary['total_records_processed']}")
    print(f"Valid records:                 {summary['total_valid_records']}")
    print(f"Invalid records:               {summary['total_invalid_records']}")
    print(f"Approved transactions:         {summary['total_approved_transactions']}")
    print(f"Declined transactions:         {summary['total_declined_transactions']}")
    print(f"Total approved value:          ${summary['total_approved_value']:,.2f}")
    print(f"Suspicious transactions:       {summary['total_suspicious_transactions']}")
    print(f"Suspicious accounts:           {summary['total_suspicious_accounts']}")
    print(f"High-value alerts:             {summary['high_value_alerts']}")
    print(f"Repeated-decline alerts:       {summary['repeated_decline_alerts']}")
    print(f"Multiple-location alerts:      {summary['multiple_location_alerts']}")
    print(f"Time-based decline alerts:     {summary['time_based_alerts']}")


def export_summary_csv(summary, filepath="summary_report.csv"):
    """
    Export summary statistics to a CSV file.

    Args:
        summary: Summary statistics dictionary.
        filepath: Output CSV file path.

    Returns:
        True if export succeeded, False otherwise.
    """
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Metric", "Value"])
            for key, value in summary.items():
                label = key.replace("_", " ").title()
                if key == "total_approved_value":
                    writer.writerow([label, f"{value:.2f}"])
                else:
                    writer.writerow([label, value])
    except OSError as exc:
        print(f"Error: Unable to export summary - {exc}")
        return False

    print(f"Summary report exported to '{filepath}'")
    return True
