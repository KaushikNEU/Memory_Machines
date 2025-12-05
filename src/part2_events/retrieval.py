# src/part2_events/retrieval.py

import json
import os
from typing import List, Dict, Any, Tuple

from .config import EventConfig


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))
    return docs


def chunk_text(text: str, max_words: int = 1000, overlap_words: int = 150) -> List[str]:
    """
    Simple word-based chunking. Keeps overlap to preserve context.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    n = len(words)

    while start < n:
        end = min(start + max_words, n)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap_words)

    return chunks


def score_chunk_for_event(chunk: str, event_cfg: EventConfig) -> int:
    """
    Naive keyword score: count occurrences of each keyword (case-insensitive).
    """
    text_lower = chunk.lower()
    score = 0
    for kw in event_cfg.keywords:
        if kw.lower() in text_lower:
            score += 1
    return score


def get_top_chunks_for_event(
    content: str,
    event_cfg: EventConfig,
    max_words: int = 1000,
    overlap_words: int = 150,
    top_k: int = 5,
) -> List[Tuple[str, int]]:
    """
    Return up to top_k (chunk, score) pairs with score > 0.
    """
    chunks = chunk_text(content, max_words=max_words, overlap_words=overlap_words)
    scored = []
    for ch in chunks:
        s = score_chunk_for_event(ch, event_cfg)
        if s > 0:
            scored.append((ch, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
