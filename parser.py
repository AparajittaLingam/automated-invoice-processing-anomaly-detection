import re 
from datetime import datetime
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
OCR_TEXT_DIR = BASE / "ocr_text"
OUTPUT_DIR = BASE / "output"

FIELDS = {
    "vendor": "Vendor",
    "invoice_number": "Invoice",
    "date": "Date",
    "currency": "Currency",
    "item": "Item",
    "quantity": "Quantity",
    "unit_price": "Unit price",
    "subtotal": "Subtotal",
    "tax": "Tax",
    "total": "Total"
}

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y"]
LOOKALIKES = str.maketrans({"O":"0","o":"0","S":"5","I":"1","l":"1","B":"8","Z":"2"})

def find_field(text, label):
    pattern = rf"^{label}:\s*(.+)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None

def fix_invoice_number(raw):
    if raw is None or not raw.startswith("INV"):
        return raw
    number_part = raw[3:].translate(LOOKALIKES)
    if number_part.isdigit():
        return f"INV{int(number_part):03d}"
    return raw

def to_number(raw):
    if raw is None:
        return None
    cleaned = raw.replace(",","").replace("$","").rstrip(".")
    try:
        return float(cleaned)
    except ValueError:
        return None

def to_date(raw):
    if raw is None:
        return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(raw, date_format).date()
        except ValueError:
            continue
    return None

def parse_invoice(text, document_id):
    raw = {column: find_field(text, label) for column, label in FIELDS.items()}
    return {
        "document_id": document_id,
        "vendor": raw["vendor"],
        "invoice_number_ocr": raw["invoice_number"], # what OCR read (kept for the report)
        "invoice_number": fix_invoice_number(raw["invoice_number"]), # corrected version
        "date": to_date(raw["date"]),
        "currency": raw["currency"],
        "item": raw["item"],
        "quantity": to_number(raw["quantity"]),
        "unit_price": to_number(raw["unit_price"]),
        "subtotal": to_number(raw["subtotal"]),
        "tax": to_number(raw["tax"]),
        "total": to_number(raw["total"])
    }

def parse_all_invoices():
    rows = []
    for text_path in sorted(OCR_TEXT_DIR.glob("*.txt")):
        text = text_path.read_text(encoding="utf-8")
        rows.append(parse_invoice(text, text_path.stem))

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / "parsed_invoices.csv", index=False)
    return df

if __name__ == "__main__":
    df = parse_all_invoices()
    print(df[["document_id","vendor","invoice_number_ocr","invoice_number","total"]].head(12))
    print("\nTable size (rows, columns): ",df.shape)
    print("\nMissing values per column:")
    print(df.isna().sum())
    print("\nInvoice numbers that dont look like INV + 3 digits: ")
    odd = df[~df["invoice_number"].str.fullmatch(r"INV\d{3}")]
    print(odd[["document_id","invoice_number_ocr","invoice_number"]])

