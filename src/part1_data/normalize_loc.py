# src/part1_data/normalize_loc.py

import json
import os
from typing import Dict, Any
from bs4 import BeautifulSoup

RAW_DIR = "data/raw/loc"
OUT_PATH = "data/processed/loc_lincoln.jsonl"

# Human hints for document_type & from/to where known
LOC_META: Dict[str, Dict[str, str]] = {
    "mal0440500": {
        "document_type": "Letter",
        "from": "Abraham Lincoln",
        # "to": "..."  # fill if you find it in the JSON or transcription
    },
    "mal0882800": {
        "document_type": "Note",
        "from": "Abraham Lincoln",
    },
    "gettysburg_nicolay": {
        "document_type": "Speech",
        "from": "Abraham Lincoln",
    },
    "mal4361300": {
        "document_type": "Speech",
        "from": "Abraham Lincoln",
    },
    "mal4361800": {
        "document_type": "Speech",
        "from": "Abraham Lincoln",
    },
}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_text_from_gettysburg_html(html_path: str) -> str:
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    # The transcription is usually within some main content div; this may need tweaking
    main = soup.find("div", {"id": "content"}) or soup.find("div", {"class": "content"})
    text = (main.get_text("\n") if main else soup.get_text("\n"))
    return text.strip()


def extract_fields_from_loc_json(loc_id: str, data: dict) -> Dict[str, str]:
    """
    LoC JSON structure can vary. We grab the most likely fields:
      - title
      - date
      - location (place)
      - transcription/full text if provided
    """
    title = ""
    date = ""
    place = ""
    content = ""

    # 1) Title: often in 'title' or 'item' fields
    if "item" in data and isinstance(data["item"], list) and data["item"]:
        title = data["item"][0].get("title", [""])[0] if isinstance(data["item"][0].get("title"), list) else data["item"][0].get("title", "")
        date = data["item"][0].get("date", "")
        place = data["item"][0].get("location", [""])[0] if isinstance(data["item"][0].get("location"), list) else data["item"][0].get("location", "")
    else:
        title = data.get("title") or ""
        date = data.get("date") or ""

    # 2) Transcription or text may appear under different keys; we do a best-effort search.
    # Depending on the real structure, you may refine this.
    candidates = []

    def collect_texts(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = k.lower()
                if any(term in kl for term in ["transcription", "text", "fulltext"]):
                    if isinstance(v, str):
                        candidates.append(v)
                collect_texts(v)
        elif isinstance(obj, list):
            for x in obj:
                collect_texts(x)

    collect_texts(data)
    if candidates:
        content = "\n\n".join(candidates)

    return {
        "title": title or f"LoC Item {loc_id}",
        "date": date or "",
        "place": place or "",
        "content": content.strip(),
    }


def normalize_loc_item(loc_id: str) -> Dict:
    meta = LOC_META.get(loc_id, {})
    doc_type = meta.get("document_type", "Unknown")
    from_field = meta.get("from", "")
    to_field = meta.get("to", "")

    json_path = os.path.join(RAW_DIR, f"{loc_id}.json")
    html_path = os.path.join(RAW_DIR, f"{loc_id}.html")

    if loc_id == "gettysburg_nicolay":
        # Special case: transcription lives in HTML
        content = extract_text_from_gettysburg_html(html_path)
        title = "Gettysburg Address (Nicolay Copy)"
        date = "1863-11-19"  # You may override or derive this from metadata if present elsewhere
        place = "Gettysburg, Pennsylvania"
    else:
        data = load_json(json_path)
        fields = extract_fields_from_loc_json(loc_id, data)
        title = fields["title"]
        date = fields["date"]
        place = fields["place"]
        content = fields["content"]

    record = {
        "id": f"loc_{loc_id}",
        "title": title,
        "reference": LOC_ITEMS_REFERENCE(loc_id),
        "document_type": doc_type,
        "date": date,   # "As in the source" – we don't change format here
        "place": place,
        "from": from_field,
        "to": to_field,
        "content": content,
    }
    return record


def LOC_ITEMS_REFERENCE(loc_id: str) -> str:
    # Mirror the original URLs used in download_loc.py
    mapping = {
        "mal0440500": "https://www.loc.gov/item/mal0440500/",
        "mal0882800": "https://www.loc.gov/resource/mal.0882800",
        "gettysburg_nicolay": "https://www.loc.gov/exhibits/gettysburg-address/ext/trans-nicolay-copy.html",
        "mal4361300": "https://www.loc.gov/resource/mal.4361300",
        "mal4361800": "https://www.loc.gov/resource/mal.4361800/",
    }
    return mapping[loc_id]


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for loc_id in LOC_META.keys():
            try:
                record = normalize_loc_item(loc_id)

                if not record["content"]:
                    # Log partial failure for your report
                    print(f"[warn] No content extracted for {loc_id}; will mention as partial in report.")

                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"[ok] Normalized LoC item {loc_id}")
            except Exception as e:
                print(f"[error] Failed to normalize {loc_id}: {e}")


if __name__ == "__main__":
    main()
