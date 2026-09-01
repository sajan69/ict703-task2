"""
Fraud detection rules module.
"""

from datetime import timedelta


def _rule_info(config, rule_key, default_name):
    """Get rule name and severity from configuration."""
    rules = config.get("rules", {})
    rule = rules.get(rule_key, {})
    return rule.get("name", default_name), rule.get("severity", "MEDIUM")


def detect_high_value(transactions, config):
    """
    Rule 1: Flag approved transactions above the high-value threshold.

    Args:
        transactions: List of valid transaction dictionaries.
        config: Configuration dictionary with thresholds.

    Returns:
        List of alert dictionaries.
    """
    threshold = config.get("high_value_threshold", 5000)
    rule_name, severity = _rule_info(config, "high_value", "High-Value Transactions")
    alerts = []

    for txn in transactions:
        if txn["status"] == "APPROVED" and txn["amount"] > threshold:
            alerts.append(
                {
                    "rule": rule_name,
                    "severity": severity,
                    "alert_type": "transaction",
                    "transaction_id": txn["transaction_id"],
                    "account_id": txn["account_id"],
                    "amount": txn["amount"],
                    "reason": (
                        f"Transaction {txn['transaction_id']} was flagged because the "
                        f"approved amount of ${txn['amount']:,.2f} exceeded the "
                        f"${threshold:,.0f} threshold."
                    ),
                }
            )

    return alerts


def detect_repeated_declined(by_account, config):
    """
    Rule 2: Flag accounts with four or more declined transactions.

    Args:
        by_account: Dictionary mapping account_id to transaction lists.
        config: Configuration dictionary with thresholds.

    Returns:
        List of alert dictionaries.
    """
    threshold = config.get("declined_count_threshold", 4)
    rule_name, severity = _rule_info(
        config, "repeated_declined", "Repeated Declined Transactions"
    )
    alerts = []

    for account_id, transactions in by_account.items():
        declined = [txn for txn in transactions if txn["status"] == "DECLINED"]
        if len(declined) >= threshold:
            txn_ids = [txn["transaction_id"] for txn in declined]
            alerts.append(
                {
                    "rule": rule_name,
                    "severity": severity,
                    "alert_type": "account",
                    "account_id": account_id,
                    "declined_count": len(declined),
                    "transaction_ids": txn_ids,
                    "reason": (
                        f"Account {account_id} was flagged because it has "
                        f"{len(declined)} declined transactions "
                        f"(threshold: {threshold})."
                    ),
                }
            )

    return alerts


def detect_multiple_locations(by_account, config):
    """
    Rule 3: Flag accounts with transactions in three or more locations.

    Args:
        by_account: Dictionary mapping account_id to transaction lists.
        config: Configuration dictionary with thresholds.

    Returns:
        List of alert dictionaries.
    """
    threshold = config.get("location_count_threshold", 3)
    rule_name, severity = _rule_info(config, "multiple_locations", "Multiple Locations")
    alerts = []

    for account_id, transactions in by_account.items():
        locations = sorted({txn["location"] for txn in transactions})
        if len(locations) >= threshold:
            txn_ids = [txn["transaction_id"] for txn in transactions]
            alerts.append(
                {
                    "rule": rule_name,
                    "severity": severity,
                    "alert_type": "account",
                    "account_id": account_id,
                    "location_count": len(locations),
                    "locations": locations,
                    "transaction_ids": txn_ids,
                    "reason": (
                        f"Account {account_id} was flagged because transactions occurred "
                        f"in {len(locations)} different locations "
                        f"(threshold: {threshold})."
                    ),
                }
            )

    return alerts


def detect_time_based_declined(by_account, config):
    """
    Rule 4 (Advanced): Flag accounts with multiple declined transactions
    within a configurable time window.

    Args:
        by_account: Dictionary mapping account_id to transaction lists.
        config: Configuration dictionary with time window settings.

    Returns:
        List of alert dictionaries.
    """
    window_minutes = config.get("time_window_minutes", 30)
    threshold = config.get("declined_in_window_threshold", 4)
    rule_name, severity = _rule_info(
        config, "time_based_declined", "Time-Based Declined Burst"
    )
    alerts = []

    for account_id, transactions in by_account.items():
        declined = sorted(
            [txn for txn in transactions if txn["status"] == "DECLINED"],
            key=lambda txn: txn["timestamp"],
        )

        if len(declined) < threshold:
            continue

        flagged = False
        flagged_ids = set()

        for index, start_txn in enumerate(declined):
            window_end = start_txn["timestamp"] + timedelta(minutes=window_minutes)
            window_txns = [
                txn
                for txn in declined[index:]
                if start_txn["timestamp"] <= txn["timestamp"] <= window_end
            ]

            if len(window_txns) >= threshold:
                flagged = True
                flagged_ids.update(txn["transaction_id"] for txn in window_txns)

        if flagged:
            alerts.append(
                {
                    "rule": rule_name,
                    "severity": severity,
                    "alert_type": "account",
                    "account_id": account_id,
                    "declined_in_window": len(flagged_ids),
                    "time_window_minutes": window_minutes,
                    "transaction_ids": sorted(flagged_ids),
                    "reason": (
                        f"Account {account_id} was flagged because it had "
                        f"{len(flagged_ids)} declined transactions within a "
                        f"{window_minutes}-minute window (threshold: {threshold})."
                    ),
                }
            )

    return alerts


def run_all_detections(transactions, by_account, config):
    """
    Run all fraud detection rules and return combined alerts.

    Args:
        transactions: List of all valid transactions.
        by_account: Dictionary grouped by account ID.
        config: Configuration settings.

    Returns:
        List of all alert dictionaries.
    """
    alerts = []
    alerts.extend(detect_high_value(transactions, config))
    alerts.extend(detect_repeated_declined(by_account, config))
    alerts.extend(detect_multiple_locations(by_account, config))
    alerts.extend(detect_time_based_declined(by_account, config))
    return alerts
