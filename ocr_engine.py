from pathlib import Path
import pytesseract
import cv2

BASE = Path(__file__).resolve().parent
CLEAN_IMAGE_DIR = BASE / "images" / "clean" # INPUT: clean images from preprocessing.py
OCR_TEXT_DIR = BASE / "ocr_text" # OUTPUT: one .txt file per invoice
TEXT_DIR = BASE / "text"     # REFERENCE: the correct text of every invoice (for measuring accuracy)

def image_to_text(image_path):
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    text = pytesseract.image_to_string(image)
    return text

def ocr_all_invoices():
    OCR_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    image_files = sorted(CLEAN_IMAGE_DIR.glob("*.png"))
    print(f"Found {len(image_files)} clean images")

    for number, image_path in enumerate(image_files, start=1):
        text = image_to_text(image_path)
        out_path = OCR_TEXT_DIR / f"{image_path.stem}.txt"
        out_path.write_text(text, encoding = "utf-8")
        print(f"[{number}/{len(image_files)}] {image_path.name} -> {out_path.name}")

    print("Done. OCR text saved to: ", OCR_TEXT_DIR)

def measure_ocr_accuracy():
    total_lines = 0
    correct_lines = 0
    mistakes = []

    for ocr_path in sorted(OCR_TEXT_DIR.glob("*.txt")):
        reference_path = TEXT_DIR / ocr_path.name
        ocr_lines = [line.strip() for line in ocr_path.read_text(encoding="utf-8").splitlines()]
        correct_text = reference_path.read_text(encoding="utf-8")

        for line in correct_text.splitlines():
            line = line.strip()
            if line == "":
                continue

            total_lines += 1
            if line in ocr_lines:
                correct_lines += 1
            else:
                label = line.split(":")[0]
                ocr_read = [l for l in ocr_lines if l.startswith(label+":")]
                mistakes.append(f"{ocr_path.stem}: expected '{line}' but OCR read {ocr_read}")

    accuracy = correct_lines / total_lines * 100
    print(f"\nLine accuracy: {correct_lines}/{total_lines} = {accuracy:.1f}%")
    print(f"Lines OCR got wrong ({len(mistakes)}): ")
    for mistake in mistakes:
        print(" ", mistake)

                

if __name__ == "__main__":
    ocr_all_invoices() #read all 48 images
    measure_ocr_accuracy() #check how accurate that was

    

