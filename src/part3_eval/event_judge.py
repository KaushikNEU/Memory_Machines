# src/part3_eval/event_judge.py

import json
import os
import sys
from typing import Dict, Any, List, Tuple

# --- Make sure src/ is on sys.path so we can import sibling packages ---

current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(os.path.dirname(current_file))  # .../src
if src_dir not in sys.path:
    sys.path.append(src_dir)

from part2_events.config import EVENTS
from part2_events.llm_client import call_llm


EVENT_CLAIMS_PATH = "data/events/event_extractions.jsonl"
OUT_PATH = "data/evals/event_consistency.jsonl"


def load_event_claims(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def group_claims_by_event(
    records: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Group event records into a structure like:

    {
      "gettysburg_address": {
        "event_name": "...",
        "lincoln": {
          "doc_ids": [...],
          "claims": [...]
        },
        "other": {
          "doc_ids": [...],
          "claims": [...]
        }
      },
      ...
    }
    """
    grouped: Dict[str, Dict[str, Any]] = {}

    for rec in records:
        event_id = rec["event"]
        source = rec.get("source", "unknown")
        doc_id = rec["doc_id"]
        claims = rec.get("claims", [])

        if event_id not in grouped:
            grouped[event_id] = {
                "event_name": rec.get(
                    "event_name",
                    EVENTS.get(event_id).name if event_id in EVENTS else event_id,
                ),
                "lincoln": {"doc_ids": [], "claims": []},
                "other": {"doc_ids": [], "claims": []},
                "unknown": {"doc_ids": [], "claims": []},
            }

        bucket = grouped[event_id].get(source, grouped[event_id]["unknown"])
        if doc_id not in bucket["doc_ids"]:
            bucket["doc_ids"].append(doc_id)
        bucket["claims"].extend(claims)

    # Deduplicate claims per source
    for grp in grouped.values():
        for src in ["lincoln", "other", "unknown"]:
            seen = set()
            unique_claims = []
            for c in grp[src]["claims"]:
                c_norm = c.strip()
                if c_norm and c_norm not in seen:
                    seen.add(c_norm)
                    unique_claims.append(c_norm)
            grp[src]["claims"] = unique_claims

    return grouped


def build_judge_prompt(
    event_id: str,
    event_name: str,
    lincoln_claims: List[str],
    other_claims: List[str],
) -> Tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for the main 3A judge.
    """
    event_cfg = EVENTS.get(event_id)
    description = event_cfg.description if event_cfg else ""

    system_prompt = (
        "You are a careful historical evaluator. Your task is to compare how "
        "Abraham Lincoln's own writings describe an event versus how later authors "
        "describe the same event. Be precise and fair. Use ONLY the claims provided."
    )

    def fmt_list(lst: List[str]) -> str:
        if not lst:
            return "  (none)\n"
        return "\n".join(f"  - {c}" for c in lst)

    lincoln_block = fmt_list(lincoln_claims)
    other_block = fmt_list(other_claims)

    user_prompt = f"""
Event: {event_name} ({event_id})

Short description:
{description}

Set A: Claims from Abraham Lincoln's own writings
{lincoln_block}

Set B: Claims from other authors (historians, biographers, etc.)
{other_block}

Your tasks:

1. Assign an OVERALL CONSISTENCY SCORE between 0 and 100, where:
   - 0 = total contradiction between Lincoln and later authors
   - 100 = perfect alignment, no meaningful contradictions

2. Identify points of AGREEMENT between Set A and Set B. List up to 5 short examples.

3. Identify points of CONTRADICTION or clear disagreement. For each, classify the type of difference as one of:
   - "factual"      (e.g., dates, numbers, locations differ)
   - "interpretive" (same facts, but different motives, causes, feelings)
   - "omission"     (Author A mentions something that B ignores)

4. Describe briefly:
   - What seems to be missing from Lincoln's own claims relative to later authors.
   - What seems to be missing from later authors relative to Lincoln.

5. Compare tone: does Lincoln sound more sympathetic, critical, neutral, or something else relative to later authors?

Return your answer as valid JSON with this EXACT structure:

{{
  "event": "{event_id}",
  "overall_consistency": <integer between 0 and 100>,
  "agreement_examples": [
    "<short agreement example 1>",
    "<short agreement example 2>"
  ],
  "contradictions": [
    {{
      "description": "<short description of the contradiction>",
      "type": "<one of: factual, interpretive, omission>"
    }}
  ],
  "missing_from_lincoln": "<brief sentence or paragraph>",
  "missing_from_others": "<brief sentence or paragraph>",
  "tone_comparison": "<brief comparison of tone between Lincoln and other authors>"
}}
"""

    return system_prompt, user_prompt


def safe_parse_judge_output(output: str, event_id: str) -> Dict[str, Any]:
    """
    Parse the judge's JSON output, with fallbacks and normalization.
    """
    text = output.strip()
    if text.startswith("```"):
        text = text.strip("`")
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    try:
        data = json.loads(text)
    except Exception:
        data = {}

    # Normalize
    if "event" not in data:
        data["event"] = event_id

    if not isinstance(data.get("overall_consistency"), (int, float)):
        data["overall_consistency"] = 50
    else:
        val = int(round(float(data["overall_consistency"])))
        data["overall_consistency"] = max(0, min(100, val))

    if not isinstance(data.get("agreement_examples"), list):
        data["agreement_examples"] = []

    # contradictions: list of {description, type}
    contras = data.get("contradictions")
    if not isinstance(contras, list):
        contras = []
    normalized_contras = []
    for c in contras:
        if not isinstance(c, dict):
            continue
        desc = str(c.get("description", "")).strip()
        ctype = str(c.get("type", "")).lower().strip()
        if ctype not in {"factual", "interpretive", "omission"}:
            # best-effort type inference
            if "date" in desc or "number" in desc or "location" in desc:
                ctype = "factual"
            elif "motive" in desc or "cause" in desc or "feeling" in desc:
                ctype = "interpretive"
            elif "mention" in desc or "ignore" in desc or "omission" in desc:
                ctype = "omission"
            else:
                ctype = "interpretive"
        if desc:
            normalized_contras.append({"description": desc, "type": ctype})
    data["contradictions"] = normalized_contras

    for key in ["missing_from_lincoln", "missing_from_others", "tone_comparison"]:
        if key not in data or not isinstance(data[key], str):
            data[key] = ""

    return data


def evaluate_events(grouped: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the LLM judge for each event where we have any claims.
    """
    results: List[Dict[str, Any]] = []

    for event_id, grp in grouped.items():
        lincoln_claims = grp["lincoln"]["claims"]
        other_claims = grp["other"]["claims"]

        if not lincoln_claims and not other_claims:
            continue

        event_name = grp["event_name"]
        print(f"[info] Evaluating event {event_id} ({event_name})")

        system_prompt, user_prompt = build_judge_prompt(
            event_id, event_name, lincoln_claims, other_claims
        )

        raw_output = call_llm(system_prompt, user_prompt, temperature=0.2)
        parsed = safe_parse_judge_output(raw_output, event_id)

        parsed["event_name"] = event_name
        parsed["lincoln_doc_ids"] = grp["lincoln"]["doc_ids"]
        parsed["other_doc_ids"] = grp["other"]["doc_ids"]
        parsed["lincoln_claim_count"] = len(lincoln_claims)
        parsed["other_claim_count"] = len(other_claims)

        results.append(parsed)

    return results


def main():
    if not os.path.exists(EVENT_CLAIMS_PATH):
        raise FileNotFoundError(f"Event claims file not found at: {EVENT_CLAIMS_PATH}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    records = load_event_claims(EVENT_CLAIMS_PATH)
    print(f"[info] Loaded {len(records)} event claim records")

    grouped = group_claims_by_event(records)
    print(f"[info] Found {len(grouped)} events with extracted claims")

    eval_results = evaluate_events(grouped)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for res in eval_results:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")

    print(f"[ok] Wrote {len(eval_results)} evaluation records to {OUT_PATH}")


if __name__ == "__main__":
    main()
