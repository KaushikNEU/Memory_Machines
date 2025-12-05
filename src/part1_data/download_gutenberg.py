# src/part1_data/download_gutenberg.py

import os
import time
from typing import List
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

GUTENBERG_BOOK_URLS: List[str] = [
    "https://www.gutenberg.org/ebooks/6812",
    "https://www.gutenberg.org/ebooks/6811",
    "https://www.gutenberg.org/ebooks/12801",
    "https://www.gutenberg.org/ebooks/14004",
    "https://www.gutenberg.org/ebooks/18379",
]

RAW_DIR = "data/raw/gutenberg"
os.makedirs(RAW_DIR, exist_ok=True)


def get_book_id(url: str) -> str:
    # "https://www.gutenberg.org/ebooks/6812" -> "6812"
    return url.rstrip("/").split("/")[-1]


def get_plain_text_url(book_page_html: str) -> str:
    """
    Parse the Gutenberg book HTML and find the 'Plain Text UTF-8' link.
    This is the 'engineering grit' part: we don't hard-code the .txt URL.
    """
    soup = BeautifulSoup(book_page_html, "html.parser")

    # Common pattern: link text contains "Plain Text UTF-8"
    for a in soup.find_all("a"):
        link_text = (a.get_text() or "").strip().lower()
        if "plain text utf-8" in link_text:
            href = a.get("href")
            if href:
                # Links are often relative like "/files/6812/6812-0.txt"
                if href.startswith("http"):
                    return href
                return "https://www.gutenberg.org" + href

    raise ValueError("Plain Text UTF-8 download link not found")


def download_gutenberg_book(book_url: str, sleep_s: float = 1.0) -> None:
    book_id = get_book_id(book_url)
    out_path = os.path.join(RAW_DIR, f"{book_id}.txt")

    if os.path.exists(out_path):
        print(f"[skip] {book_id} already downloaded")
        return

    print(f"[info] Fetching book page for {book_id} ...")
    resp = requests.get(book_url, timeout=30)
    resp.raise_for_status()

    text_url = get_plain_text_url(resp.text)
    print(f"[info] Found text URL for {book_id}: {text_url}")

    time.sleep(sleep_s)
    text_resp = requests.get(text_url, timeout=60)
    text_resp.raise_for_status()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text_resp.text)

    print(f"[ok] Saved {book_id} -> {out_path}")


def main():
    for url in tqdm(GUTENBERG_BOOK_URLS):
        try:
            download_gutenberg_book(url)
        except Exception as e:
            print(f"[error] Failed to download {url}: {e}")


if __name__ == "__main__":
    main()
