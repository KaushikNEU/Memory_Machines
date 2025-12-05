# src/part2_events/event_extractor.py

import json
import os
import sys
from typing import Dict, Any, List

# --- Import handling: works both as a module and a script ---

if __package__ is None or __package__ == "":
    # Running as a script: add src/ to sys.path and use absolute imports
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(os.path.dirname(current_file))  # .../src
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from part2_events.config import get_all_events
    from part2_events.retrieval import load_jsonl, get_top_chunks_for_event
    from part2_events.llm_client import call_llm
else:
    # Running as a module: use relative imports
    from .config import get_all_events
    from .retrieval import load_jsonl, get_top_chunks_for_event
    from .llm_client import call_llm


GUTENBERG_PATH = "data/processed/gutenberg_lincoln.jsonl"
LOC_PATH = "data/processed/loc_lincoln_improved.jsonl"
OUT_PATH = "data/events/event_extractions.jsonl"

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)


def classify_source(doc_id: str) -> str:
    """
    Simple source type classifier:
      - 'loc_' => 'lincoln' (first-person or close)
      - 'gutenberg_' => 'other' (secondary authors)
    """
    if doc_id.startswith("loc_"):
        return "lincoln"
    if doc_id.startswith("gutenberg_"):
        return "other"
    return "unknown"


def build_extraction_prompt(
    event_id: str,
    event_name: str,
    event_description: str,
    combined_context: str,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt)
    """
    system_prompt = (
        "You are a careful historian extracting factual and interpretive claims "
        "about key events in Abraham Lincoln's life. You must only use the provided "
        "text and avoid speculation. Return concise JSON only."
    )

    user_prompt = f"""
Event: {event_name} ({event_id})

Event description:
{event_description}

Task:
1. From the text below, list all concrete claims related to this event.
   - Each claim should be a short, self-contained sentence.
   - Include both factual statements and interpretive statements (e.g., about motives or attitudes).
2. Extract any dates, times, and places mentioned specifically for this event.
3. Classify the tone of the author toward Lincoln in this context as one of:
   "Sympathetic", "Critical", "Neutral", "Mixed", or "Not discussed".

Text:
\"\"\" 
{combined_context}
\"\"\" 

Return your answer as valid JSON with this exact structure:

{{
  "claims": [ "<claim 1>", "<claim 2>", "..."],
  "temporal_details": {{
    "date": "<date if given, else empty string>",
    "time": "<time if given, else empty string>",
    "place": "<place if given, else empty string>"
  }},
  "tone": "<one of: Sympathetic, Critical, Neutral, Mixed, Not discussed>"
}}
"""

    return system_prompt, user_prompt


def safe_parse_json(output: str) -> Dict[str, Any]:
    """
    Try to parse model output as JSON.
    If the model wraps JSON in code fences or extra text, strip it.
    """
    text = output.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.strip("`")
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except Exception:
        # Fallback to empty structure if parsing fails
        data = {
            "claims": [],
            "temporal_details": {"date": "", "time": "", "place": ""},
            "tone": "Not discussed",
        }

    # Normalize structure
    if "claims" not in data or not isinstance(data["claims"], list):
        data["claims"] = []
    if "temporal_details" not in data or not isinstance(data["temporal_details"], dict):
        data["temporal_details"] = {"date": "", "time": "", "place": ""}
    for key in ["date", "time", "place"]:
        if key not in data["temporal_details"]:
            data["temporal_details"][key] = ""

    if "tone" not in data or not isinstance(data["tone"], str):
        data["tone"] = "Not discussed"

    return data


def extract_for_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For a single document, run extraction for all events.
    Returns a list of event result records.
    """
    results: List[Dict[str, Any]] = []
    doc_id = doc["id"]
    source = classify_source(doc_id)
    title = doc.get("title", "")
    content = doc.get("content", "")

    for event_cfg in get_all_events():
        # Retrieve top chunks for this event
        top_chunks = get_top_chunks_for_event(content, event_cfg, top_k=5)
        if not top_chunks:
            # No sign of this event in the document
            continue

        # Concatenate chunks with separators
        combined_context = "\n\n---\n\n".join(ch for ch, _ in top_chunks)

        system_prompt, user_prompt = build_extraction_prompt(
            event_cfg.event_id,
            event_cfg.name,
            event_cfg.description,
            combined_context,
        )

        raw_output = call_llm(system_prompt, user_prompt)
        parsed = safe_parse_json(raw_output)

        record = {
            "event": event_cfg.event_id,
            "event_name": event_cfg.name,
            "doc_id": doc_id,
            "source": source,  # "lincoln" or "other"
            "document_title": title,
            "claims": parsed["claims"],
            "temporal_details": parsed["temporal_details"],
            "tone": parsed["tone"],
        }
        results.append(record)

    return results


def main():
    gutenberg_docs = load_jsonl(GUTENBERG_PATH)
    loc_docs = load_jsonl(LOC_PATH)
    all_docs = gutenberg_docs + loc_docs

    total_docs = len(all_docs)
    print(f"[info] Loaded {total_docs} documents")

    count_records = 0
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    with open(OUT_PATH, "w", encoding="utf-8") as out_f:
        for i, doc in enumerate(all_docs, start=1):
            print(f"[info] Processing doc {i}/{total_docs}: {doc.get('id')} - {doc.get('title')}")
            try:
                doc_results = extract_for_document(doc)
                for rec in doc_results:
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count_records += 1
            except Exception as e:
                print(f"[error] Failed on doc {doc.get('id')}: {e}")

    print(f"[ok] Wrote {count_records} event records to {OUT_PATH}")


if __name__ == "__main__":
    main()
