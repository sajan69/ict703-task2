# ICT703 Task 2 — Bank Transaction Fraud Detection System

A Python application that reads fictional bank transaction records, validates them, detects suspicious activity using configurable fraud rules, and generates summary reports.

> **Note:** This is a fictional scenario created for ICT703 Assessment Task 2. All banks, accounts, customers, and transactions are fictional.

## Features

### Core Features
- Read and process pipe-delimited transaction files
- Validate transaction records (field count, types, amounts, status)
- Store valid transactions in memory using lists and dictionaries
- Detect suspicious activity using three core fraud rules
- Display flagged transactions and accounts with explanations

### Advanced Features (High Distinction)
| Feature | Description |
|---------|-------------|
| Enhanced Data Validation | Regex format checks, duplicate ID detection, invalid record CSV export |
| Time-Based Fraud Detection | Flags 4+ declined transactions within a 30-minute window |
| Configurable Fraud Rules | All thresholds loaded from `config.json` |
| Summary Statistics | Console summary + CSV export (`summary_report.csv`) |

## Project Structure

```
Task 2/
├── README.md
├── pyproject.toml              # uv project config
├── uv.lock                     # Locked dependencies
├── .python-version             # Python version for uv
└── program/                    # Python submission (ZIP this folder)
    ├── main.py                 # Entry point
    ├── file_handler.py         # File reading and error handling
    ├── validator.py            # Core + enhanced validation
    ├── storage.py              # Transaction storage (list + dict)
    ├── fraud_detector.py       # Fraud detection rules 1–4
    ├── config_loader.py        # JSON configuration loader
    ├── reporter.py             # Alerts, summary, CSV export
    ├── config.json             # Configurable fraud thresholds
    ├── transactions.txt        # Sample transaction dataset
    ├── transactions_empty.txt  # Empty file for testing
    └── test.py                 # Automated test suite (22 tests)
```

## Requirements

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — Python package and project manager
- **Program:** Python Standard Library only (no extra packages)

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then from the project root:

```powershell
cd "Task 2"
uv sync
```

This creates a `.venv/` virtual environment. The program runs with no extra dependencies.

## Quick Start

### Run the fraud detection program

```powershell
uv run python program/main.py
```

### Run the test suite

```powershell
uv run python program/test.py
```

Expected output: **22/22 tests pass**.

You can also run directly from `program/` with system Python (no uv required):

```powershell
cd program
python main.py
python test.py
```

## Configuration

Fraud detection thresholds are defined in [`program/config.json`](program/config.json):

| Setting | Default | Description |
|---------|---------|-------------|
| `high_value_threshold` | 5000 | Approved amount above this is flagged |
| `declined_count_threshold` | 4 | Declined transactions per account to flag |
| `location_count_threshold` | 3 | Different locations per account to flag |
| `time_window_minutes` | 30 | Time window for declined burst detection |
| `declined_in_window_threshold` | 4 | Declined txns in window to flag |

## Fraud Detection Rules

| Rule | Trigger | Default Threshold |
|------|---------|-------------------|
| High-Value Transactions | APPROVED amount exceeds threshold | $5,000 |
| Repeated Declined | Account has N+ declined transactions | 4 |
| Multiple Locations | Account has transactions in N+ locations | 3 |
| Time-Based Declined Burst | N+ declined within time window | 4 in 30 min |

## Transaction Data Format

Each record is pipe-delimited with 7 fields:

```
timestamp | transaction_id | account_id | transaction_type | amount | location | status
```

Example:

```
2026-07-11 09:15:23 | T1001 | A10025 | TRANSFER | 850.00 | Brisbane | APPROVED
```

**Valid transaction types:** TRANSFER, CARD_PAYMENT, CASH_WITHDRAWAL, ONLINE_PURCHASE, DIRECT_DEBIT

**Valid statuses:** APPROVED, DECLINED, PENDING

## Sample Data

[`program/transactions.txt`](program/transactions.txt) includes:

- Normal approved transactions
- High-value transaction (T1002, $6,500)
- Account with 5+ declined transactions (A55555)
- Account with 4+ locations (A77777, A88888)
- Time-based declined burst (A33333)
- Normal unflagged account (A99999)
- Invalid records (bad format, duplicate IDs, invalid types, etc.)

## Testing

The test suite in [`program/test.py`](program/test.py) covers:

- File reading (valid, missing, empty)
- Validation (field count, types, amounts, timestamps, duplicates)
- Fraud detection (all 4 rules + normal account not flagged)
- Configuration loading
- Summary statistics and CSV export
- Full pipeline integration

Each test prints: feature, input, expected, actual, and PASS/FAIL outcome.

## Canvas Submission

Submit the **Python ZIP** to Canvas: contents of the `program/` folder only.

To create the ZIP:

```powershell
cd program
Compress-Archive -Path * -DestinationPath "../Sajan Adhikari - Task 2.zip"
```

Ensure `main.py` is at the ZIP root, not inside a subfolder. Do **not** include `pyproject.toml` or `uv.lock` in the ZIP.

## Author

- **Student Name:** Sajan Adhikari
- **Student ID:** s_a325
- **Tutor:** Tianwa Chen
- **Course:** ICT703 Programming — 2026 Trimester 2
- **GitHub Repository:** https://github.com/sajan69/ict703-task2

## License

This project is submitted as coursework for ICT703 Programming at the University of the Sunshine Coast.
