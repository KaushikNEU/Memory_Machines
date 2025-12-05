# src/part1_data/download_loc.py

import json
import os
import time
from typing import Dict
import requests
from bs4 import BeautifulSoup

RAW_DIR = "data/raw/loc"
os.makedirs(RAW_DIR, exist_ok=True)

LOC_ITEMS: Dict[str, str] = {
    "mal0440500": "https://www.loc.gov/item/mal0440500/",  # Election Night letter
    "mal0882800": "https://www.loc.gov/resource/mal.0882800",  # Fort Sumter decision
    "gettysburg_nicolay": "https://www.loc.gov/exhibits/gettysburg-address/ext/trans-nicolay-copy.html",
    "mal4361300": "https://www.loc.gov/resource/mal.4361300",  # Second Inaugural
    "mal4361800": "https://www.loc.gov/resource/mal.4361800/",  # Last Public Address
}


def fetch_json(url: str) -> dict:
    """Try to fetch LoC JSON (for /item/ or /resource/ when supported)."""
    json_url = url.rstrip("/") + "/?fo=json"
    resp = requests.get(json_url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_json(raw_id: str, data: dict) -> None:
    out_path = os.path.join(RAW_DIR, f"{raw_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[ok] Saved JSON for {raw_id} -> {out_path}")


def save_html(raw_id: str, html: str) -> None:
    out_path = os.path.join(RAW_DIR, f"{raw_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[ok] Saved HTML for {raw_id} -> {out_path}")


def download_loc_items(sleep_s: float = 0.5):
    for loc_id, url in LOC_ITEMS.items():
        print(f"[info] Processing {loc_id} ({url})")
        try:
            if "gettysburg-address" in url:
                # Gettysburg transcription page is static HTML
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                save_html(loc_id, resp.text)
            else:
                # Try JSON API for item/resource
                data = fetch_json(url)
                save_json(loc_id, data)
        except Exception as e:
            print(f"[error] Failed to download {loc_id}: {e}")

        time.sleep(sleep_s)


def main():
    download_loc_items()


if __name__ == "__main__":
    main()
