"""
Transaction storage module using lists and dictionaries.
"""


class TransactionStore:
    """Stores valid and invalid transaction records in memory."""

    def __init__(self):
        self.transactions = []
        self.by_account = {}
        self.invalid_records = []

    def add_transaction(self, transaction):
        """Add a valid transaction to storage."""
        self.transactions.append(transaction)
        account_id = transaction["account_id"]
        if account_id not in self.by_account:
            self.by_account[account_id] = []
        self.by_account[account_id].append(transaction)

    def add_invalid(self, invalid_record):
        """Track an invalid record."""
        self.invalid_records.append(invalid_record)

    def load_valid_transactions(self, valid_transactions):
        """Load a list of valid transactions into storage."""
        for transaction in valid_transactions:
            self.add_transaction(transaction)

    def get_by_account(self, account_id):
        """Return all transactions for a given account."""
        return self.by_account.get(account_id, [])

    def get_all_accounts(self):
        """Return all account IDs with stored transactions."""
        return list(self.by_account.keys())

    def count(self):
        """Return the number of valid transactions stored."""
        return len(self.transactions)
