"""
File handling module for reading transaction data files.
"""

from pathlib import Path


def read_transaction_file(filepath):
    """
    Read transaction records from a text file.

    Args:
        filepath: Path to the transaction file.

    Returns:
        A tuple of (lines, error_message). lines is a list of raw strings
        with original line numbers preserved via index+1. error_message is
        None on success, or a descriptive string on failure.
    """
    path = Path(filepath)

    if not path.exists():
        return [], f"Error: File not found - '{filepath}'"

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], f"Error: Unable to read file '{filepath}' - {exc}"

    if not content.strip():
        return [], f"Error: File is empty - '{filepath}'"

    lines = content.splitlines()
    non_blank = [line for line in lines if line.strip()]

    if not non_blank:
        return [], f"Error: File contains no transaction records - '{filepath}'"

    return lines, None
