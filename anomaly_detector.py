from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
PARSED_CSV = BASE / "output" / "parsed_invoices.csv"  # INPUT: table from parser.py

AS_OF = pd.Timestamp("2025-04-01")
MAX_AGE_DAYS = 90
TOLERANCE = 0.01
REQUIRED = ["vendor","invoice_number","date","currency","quantity","unit_price","subtotal","total"]

def check_rules(row):
    reasons = []

    # Rule 1: missing fields
    for column in REQUIRED:
        if pd.isna(row[column]):
            reasons.append(f"missing_{column}")
    if pd.isna(row["tax"]):
        reasons.append("missing_tax")

    # Rule 2: quantity x unit price = subtotal?
    if pd.notna(row["quantity"]) and pd.notna(row["unit_price"]) and pd.notna(row["subtotal"]):
        expected_subtotal = row["quantity"] * row["unit_price"]
        if abs(expected_subtotal - row["subtotal"]) > TOLERANCE:
            reasons.append("line_total_mismatch")

    # Rule 3: subtotal + tax = total?
    if pd.notna(row["subtotal"]) and pd.notna(row["tax"]) and pd.notna(row["total"]):
        expected_total = row["subtotal"]+row["tax"]
        if abs(expected_total - row["total"]) > TOLERANCE:
            reasons.append("total_mismatch")

    # Rule 4: dates
    if pd.notna(row["date"]):
        if row["date"] > AS_OF:
            reasons.append("future_date")
        elif (AS_OF - row["date"]).days > MAX_AGE_DAYS:
            reasons.append("older_than_90_days")

    return reasons

def run_rule_checks(df):
    df["rule_reasons"] = df.apply(check_rules, axis=1)
    return df

if __name__ == "__main__":
    df = pd.read_csv(PARSED_CSV, parse_dates=["date"])
    df = run_rule_checks(df)

    flagged = df[df["rule_reasons"].str.len() > 0]
    print(f"Rule checks flagged {len(flagged)} of {len(df)} invoices:\n")
    print(flagged[["document_id","vendor","invoice_number","date","subtotal","tax","total","rule_reasons"]].to_string())
