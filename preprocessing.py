from pathlib import Path
import numpy as np
import pymupdf
import cv2

BASE = Path(__file__).resolve().parent
PDF_DIR = BASE / "documents"
RAW_IMAGE_DIR = BASE / "images" / "raw"
STAGE_DIR = BASE / "images" / "stages"
CLEAN_IMAGE_DIR = BASE / "images" / "clean"   # cleaned images, ready for OCR


def pdf_to_image(pdf_path, output_dir, dpi = 300):
    output_dir.mkdir(parents =True, exist_ok=True)

    doc = pymupdf.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    out_path = output_dir / f"{pdf_path.stem}.png"
    pix.save(out_path)
    doc.close()

    return out_path

def simulate_scan(image, seed=2):
    rng = np.random.default_rng(seed)
    scan = image.astype(np.float32)
    scan = scan * 0.80 + 15
    scan = scan + rng.normal(0, 25, scan.shape)
    specks = rng.random(scan.shape[:2])
    scan[specks < 0.01] = 0
    scan[specks > 0.99] = 255
    return np.clip(scan, 0, 255).astype(np.uint8)

def to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def reduce_noise(gray):
    return cv2.medianBlur(gray, 3)

def binarize(gray):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def clean_image(image):
    gray = to_grayscale(image)
    denoised = reduce_noise(gray)
    return binarize(denoised)

def process_all_invoices():
    CLEAN_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} invoice PDFs")

    for number, pdf_path in enumerate(pdf_files, start=1):
        raw_path = pdf_to_image(pdf_path, RAW_IMAGE_DIR)
        image = cv2.imread(str(raw_path))

        seed = int(pdf_path.stem[1:])
        scan = simulate_scan(image, seed=seed)
        clean = clean_image(scan)
        cv2.imwrite(str(CLEAN_IMAGE_DIR / f"{pdf_path.stem}.png"), clean)
        print(f"[{number}/{len(pdf_files)}] {pdf_path.name} -> cleaned")

    print("Done. Cleaned images saved to: ", CLEAN_IMAGE_DIR)

def save_stage_examples():
    """Save before/after pictures of D001 for the report."""
    raw_path = pdf_to_image(PDF_DIR / "D001.pdf", RAW_IMAGE_DIR)
    scan = simulate_scan(cv2.imread(str(raw_path)))
    gray = to_grayscale(scan)
    denoised = reduce_noise(gray)
    binary = binarize(denoised)

    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(STAGE_DIR / "1_scan.png"), scan)
    cv2.imwrite(str(STAGE_DIR / "2_gray.png"), gray)
    cv2.imwrite(str(STAGE_DIR / "3_denoised.png"), denoised)
    cv2.imwrite(str(STAGE_DIR / "4_binary.png"), binary)
    print("Saved stage examples to: ", STAGE_DIR)

if __name__ == "__main__":
    save_stage_examples()
    process_all_invoices()
