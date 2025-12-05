# src/part1_data/improve_loc_dataset.py

import json
import os
import re
from typing import Dict, Any

from bs4 import BeautifulSoup

INPUT_PATH = "data/processed/loc_lincoln.jsonl"
OUTPUT_PATH = "data/processed/loc_lincoln_improved.jsonl"

# Hand-curated metadata overrides/fills.
# These only apply when the existing field is empty.
# IMPORTANT: Fill the TODOs using the exact wording / date from LoC once you look it up.
MANUAL_META: Dict[str, Dict[str, str]] = {
    # Election Night 1860 letter
    "loc_mal0440500": {
        # TODO: Replace [Recipient] and date formatting using the LoC page.
        # Example once you verify: "Abraham Lincoln to Thurlow Weed, November 6, 1860"
        "title": "Abraham Lincoln to [Recipient], [Election Night 1860]",
        # TODO: Put the date exactly as LoC formats it, e.g. "November 6, 1860"
        "date": "",
        # TODO: If LoC gives a location (e.g. "Springfield, Illinois"), put it here
        "place": "",
        "document_type": "Letter",
        "from": "Abraham Lincoln",
        # TODO: Replace with the actual recipient name from LoC (if given)
        "to": "",
    },

    # Fort Sumter / Chew letter
    "loc_mal0882800": {
        # This is *not* Lincoln writing; it's Chew to Lincoln.
        "title": "Robert S. Chew to Abraham Lincoln, April 8, 1861",
        # You can keep this human-readable format; LoC often uses similar style.
        "date": "April 8, 1861",
        # If LoC uses slightly different punctuation (e.g. "Charleston, S.C."), feel free to adjust.
        "place": "Charleston, S.C.",
        "document_type": "Letter",
        "from": "Robert S. Chew",
        "to": "Abraham Lincoln",
    },

    # Gettysburg Address (Nicolay copy)
    "loc_gettysburg_nicolay": {
        "title": "Gettysburg Address (Nicolay Copy)",
        "date": "November 19, 1863",
        "place": "Gettysburg, Pennsylvania",
        "document_type": "Speech",
        "from": "Abraham Lincoln",
        "to": "",
    },

    # Second Inaugural Address
    "loc_mal4361300": {
        "title": "Second Inaugural Address",
        "date": "March 4, 1865",
        "place": "Washington, D.C.",
        "document_type": "Speech",
        "from": "Abraham Lincoln",
        "to": "",
    },

    # Last Public Address
    "loc_mal4361800": {
        "title": "Last Public Address",
        # TODO: Fill exact LoC wording, e.g. "April 11, 1865"
        "date": "",
        "place": "Washington, D.C.",
        "document_type": "Speech",
        "from": "Abraham Lincoln",
        "to": "",
    },
}


def looks_like_xml(content: str) -> bool:
    """
    Heuristic: if the content contains XML/HTML-style tags,
    we treat it as markup and try to strip tags.
    """
    if not content:
        return False
    return ("<" in content and ">" in content and "</" in content)


def clean_content_xml_to_text(content: str) -> str:
    """
    Convert XML / HTML-ish content into plain text while preserving line breaks.
    If it doesn't look like XML, just strip leading/trailing whitespace.
    """
    if not looks_like_xml(content):
        return content.strip()

    # Use XML parser; BeautifulSoup will handle slightly messy markup.
    soup = BeautifulSoup(content, "lxml-xml")
    text = soup.get_text("\n")

    # Collapse blanks and trim
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # drop empty lines
    return "\n".join(lines).strip()


MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
)


def maybe_extract_date_from_text(content: str) -> str:
    """
    Lightweight attempt to pull a date-like line out of the text
    if 'date' is empty. We look for a line containing a month + year.
    """
    for line in content.splitlines():
        line_stripped = line.strip()
        if any(m in line_stripped for m in MONTHS) and re.search(r"\b(18[0-9]{2}|19[0-9]{2})\b", line_stripped):
            # e.g. "April 8th, 1861" or "March 4, 1865"
            return line_stripped
    return ""


def maybe_extract_place_from_text(content: str) -> str:
    """
    Tiny heuristic for place: LoC transcriptions often start with something like:
      'Charleston S. C. April 8th 1861'
    We grab the part before the month name.
    """
    for line in content.splitlines():
        line_stripped = line.strip()
        if any(m in line_stripped for m in MONTHS):
            for m in MONTHS:
                if m in line_stripped:
                    before = line_stripped.split(m, 1)[0].strip()
                    if before:
                        return before.rstrip(",.;")
    return ""


def merge_manual_meta(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill empty metadata fields using MANUAL_META if available for the given id.
    Only overwrite fields that are currently empty or whitespace.
    """
    meta = MANUAL_META.get(record["id"], {})
    for field in ["title", "date", "place", "from", "to", "document_type"]:
        if field in meta and meta[field]:
            if not record.get(field) or not record[field].strip():
                record[field] = meta[field]
    return record


def improve_record(record: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Clean content (but never destroy existing non-empty content)
    original_content = record.get("content", "")
    cleaned_content = clean_content_xml_to_text(original_content)

    # Safety: if cleaning produced nothing but original had text, keep original
    if not cleaned_content.strip() and original_content.strip():
        cleaned_content = original_content.strip()

    record["content"] = cleaned_content

    # 2) Use manual metadata where present
    record = merge_manual_meta(record)

    # 3) If date is still empty, try to guess from content
    if not record.get("date") or not record["date"].strip():
        guessed_date = maybe_extract_date_from_text(cleaned_content)
        if guessed_date:
            record["date"] = guessed_date

    # 4) If place is still empty, try to guess from content
    if not record.get("place") or not record["place"].strip():
        guessed_place = maybe_extract_place_from_text(cleaned_content)
        if guessed_place:
            record["place"] = guessed_place

    return record


def main():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    total = 0
    improved_dates = 0
    improved_places = 0

    with open(INPUT_PATH, "r", encoding="utf-8") as in_f, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as out_f:

        for line in in_f:
            line = line.strip()
            if not line:
                continue

            rec = json.loads(line)
            before_date = rec.get("date", "").strip()
            before_place = rec.get("place", "").strip()

            rec = improve_record(rec)

            after_date = rec.get("date", "").strip()
            after_place = rec.get("place", "").strip()

            if not before_date and after_date:
                improved_dates += 1
            if not before_place and after_place:
                improved_places += 1

            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            total += 1

    print(f"[ok] Wrote improved file -> {OUTPUT_PATH}")
    print(f"[stats] Records processed: {total}")
    print(f"[stats] Dates newly filled: {improved_dates}")
    print(f"[stats] Places newly filled: {improved_places}")


if __name__ == "__main__":
    main()
