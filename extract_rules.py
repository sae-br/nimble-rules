import fitz  # PyMuPDF
import json
import os

def extract_chunks(pdf_path, output_json):
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_number = page_num + 1

        blocks = page.get_text("blocks")
        for block in blocks:
            text = block[4].strip()
            if len(text) > 40:
                all_chunks.append({
                    "text": text,
                    "page": page_number,
                    "source": os.path.basename(pdf_path)
                })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted {len(all_chunks)} blocks from {pdf_path}")


if __name__ == "__main__":
    # Re-process all 3 rulebooks
    extract_chunks("data/CoreRules-2.0.1.pdf", "output/core_rules.json")
    extract_chunks("data/GMguide-2.0.2.pdf", "output/gm_guide.json")
    extract_chunks("data/Heroes-2.0.1.pdf", "output/heroes_guide.json")

