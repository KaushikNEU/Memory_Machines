# src/part1_data/normalize_gutenberg.py

import json
import os
from typing import Dict

RAW_DIR = "data/raw/gutenberg"
OUT_PATH = "data/processed/gutenberg_lincoln.jsonl"

# Map Gutenberg ID -> human title (you can refine these by scraping each book page too)
GUTENBERG_META: Dict[str, Dict[str, str]] = {
    "6812": {"title": "Abraham Lincoln: A History, Volume 1", "document_type": "Book"},
    "6811": {"title": "Abraham Lincoln: A History, Volume 2", "document_type": "Book"},
    "12801": {"title": "Abraham Lincoln and the Union", "document_type": "Book"},
    "14004": {"title": "The Life and Public Service of Abraham Lincoln", "document_type": "Book"},
    "18379": {"title": "Abraham Lincoln: A History, Volume 3", "document_type": "Book"},
}


def strip_gutenberg_boilerplate(text: str) -> str:
    """
    Lightly strip Gutenberg header/footer while keeping the body faithful.
    This is optional, but it's a common pattern.
    We *don't* do heavy cleaning; just remove clearly-marked boilerplate.
    """
    lines = text.splitlines()
    start_idx = 0
    end_idx = len(lines)

    for i, line in enumerate(lines):
        if "*** START OF THIS PROJECT GUTENBERG EBOOK" in line.upper():
            start_idx = i + 1
            break

    for j in range(len(lines) - 1, -1, -1):
        if "*** END OF THIS PROJECT GUTENBERG EBOOK" in lines[j].upper():
            end_idx = j
            break

    body = "\n".join(lines[start_idx:end_idx]).strip()
    return body if body else text.strip()


def normalize_book(book_id: str, raw_text: str) -> Dict:
    meta = GUTENBERG_META.get(book_id, {})
    title = meta.get("title", f"Gutenberg Book {book_id}")
    document_type = meta.get("document_type", "Book")

    content = strip_gutenberg_boilerplate(raw_text)

    # Gutenberg books usually don't have per-letter metadata
    # We'll leave date/place/from/to empty strings, but consistently so.
    record = {
        "id": f"gutenberg_{book_id}",
        "title": title,
        "reference": f"https://www.gutenberg.org/ebooks/{book_id}",
        "document_type": document_type,
        "date": "",
        "place": "",
        "from": "",
        "to": "",
        "content": content,
    }
    return record


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for fname in os.listdir(RAW_DIR):
            if not fname.endswith(".txt"):
                continue
            book_id = fname.replace(".txt", "")
            raw_path = os.path.join(RAW_DIR, fname)
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            record = normalize_book(book_id, raw_text)
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[ok] Normalized Gutenberg book {book_id}")


if __name__ == "__main__":
    main()
