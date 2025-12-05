# src/part3_eval/event_judge_experiments.py

import json
import os
import sys
import statistics
from typing import Dict, Any, List, Tuple

# --- Ensure src/ is on sys.path ---

current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(os.path.dirname(current_file))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from part2_events.config import EVENTS
from part2_events.llm_client import call_llm
from part3_eval.event_judge import load_event_claims, group_claims_by_event


EVENT_CLAIMS_PATH = "data/events/event_extractions.jsonl"
PROMPT_ROBUST_OUT = "data/evals/prompt_robustness.jsonl"
SELF_CONSIST_OUT = "data/evals/self_consistency.jsonl"
INTER_RATER_OUT = "data/evals/inter_rater.jsonl"
KAPPA_OUT = "data/evals/kappa_inter_rater.jsonl"


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------

def build_strategy_prompt(
    event_id: str,
    event_name: str,
    lincoln_claims: List[str],
    other_claims: List[str],
    strategy: str,
) -> Tuple[str, str]:
    """
    Same evaluation task, but with different prompting strategies:
      - zero_shot
      - cot (chain-of-thought)
      - few_shot
    """
    event_cfg = EVENTS.get(event_id)
    description = event_cfg.description if event_cfg else ""

    def fmt_list(lst: List[str]) -> str:
        if not lst:
            return "  (none)\n"
        return "\n".join(f"  - {c}" for c in lst)

    lincoln_block = fmt_list(lincoln_claims)
    other_block = fmt_list(other_claims)

    base_system = (
        "You are a careful historical evaluator comparing Abraham Lincoln's own "
        "claims with those of later authors."
    )

    if strategy == "cot":
        base_system += " Think step by step before producing your final JSON answer."
    elif strategy == "few_shot":
        base_system += (
            " First study the example of how to compare two claim sets. Then apply the same format."
        )

    example_block = ""
    if strategy == "few_shot":
        # In the actual file this can be a full example; shortened here for clarity
        example_block = """
Example:

Set A (Lincoln):
  - Lincoln says he aims to preserve the Union above all.

Set B (Others):
  - Historians agree Lincoln prioritized Union preservation.

Correct JSON output for this simple example:

{
  "event": "example_event",
  "overall_consistency": 95,
  "agreement_examples": [
    "Both sets affirm Lincoln's primary goal is preserving the Union."
  ],
  "contradictions": [],
  "missing_from_lincoln": "Lincoln does not discuss broader international reactions.",
  "missing_from_others": "Historians do not quote Lincoln's exact phrasing.",
  "tone_comparison": "Both are broadly sympathetic to Lincoln."
}
"""

    system_prompt = base_system

    user_prompt = f"""
Event: {event_name} ({event_id})

Short description:
{description}

{example_block}

Now evaluate the REAL data below.

Set A: Claims from Abraham Lincoln's own writings
{lincoln_block}

Set B: Claims from other authors (historians, biographers, etc.)
{other_block}

Follow the same JSON format as in the example (where applicable):

- overall_consistency: integer 0–100
- agreement_examples: list of short strings
- contradictions: list of objects with 'description' and 'type' (factual, interpretive, omission)
- missing_from_lincoln: short text
- missing_from_others: short text
- tone_comparison: short text
"""

    return system_prompt, user_prompt


def extract_consistency_from_output(output: str) -> int:
    """
    Extract just the overall_consistency score from the model output.
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
        return 50

    val = data.get("overall_consistency", 50)
    try:
        v = int(round(float(val)))
        return max(0, min(100, v))
    except Exception:
        return 50


# ----------------------------------------------------------------------
# 3B.1: Prompt robustness
# ----------------------------------------------------------------------

def run_prompt_robustness(grouped: Dict[str, Dict[str, Any]]) -> None:
    """
    3B.1: Prompt robustness – compare multiple prompting strategies.
    """
    os.makedirs(os.path.dirname(PROMPT_ROBUST_OUT), exist_ok=True)
    strategies = ["zero_shot", "cot", "few_shot"]

    with open(PROMPT_ROBUST_OUT, "w", encoding="utf-8") as f_out:
        for event_id, grp in grouped.items():
            lincoln_claims = grp["lincoln"]["claims"]
            other_claims = grp["other"]["claims"]
            if not lincoln_claims and not other_claims:
                continue

            event_name = grp["event_name"]
            print(f"[robustness] Event {event_id} ({event_name})")

            for strat in strategies:
                sys_prompt, user_prompt = build_strategy_prompt(
                    event_id, event_name, lincoln_claims, other_claims, strat
                )
                raw = call_llm(sys_prompt, user_prompt, temperature=0.2)
                score = extract_consistency_from_output(raw)

                record = {
                    "event": event_id,
                    "event_name": event_name,
                    "strategy": strat,
                    "overall_consistency": score,
                }
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# 3B.2: Self-consistency
# ----------------------------------------------------------------------

def run_self_consistency(grouped: Dict[str, Dict[str, Any]]) -> None:
    """
    3B.2: Self-consistency – run the same prompt multiple times with temp>0.
    """
    os.makedirs(os.path.dirname(SELF_CONSIST_OUT), exist_ok=True)

    with open(SELF_CONSIST_OUT, "w", encoding="utf-8") as f_out:
        for event_id, grp in grouped.items():
            lincoln_claims = grp["lincoln"]["claims"]
            other_claims = grp["other"]["claims"]
            if not lincoln_claims and not other_claims:
                continue

            event_name = grp["event_name"]
            print(f"[self-consistency] Event {event_id} ({event_name})")

            sys_prompt, user_prompt = build_strategy_prompt(
                event_id, event_name, lincoln_claims, other_claims, strategy="cot"
            )

            scores: List[int] = []
            for run_idx in range(5):
                raw = call_llm(sys_prompt, user_prompt, temperature=0.7)
                score = extract_consistency_from_output(raw)
                scores.append(score)

            mean_score = sum(scores) / len(scores)
            std = float(statistics.pstdev(scores)) if len(scores) > 1 else 0.0
            coef_var = float(std / mean_score) if mean_score > 0 else 0.0

            record = {
                "event": event_id,
                "event_name": event_name,
                "strategy": "cot",
                "runs": scores,
                "mean": mean_score,
                "min": min(scores),
                "max": max(scores),
                "std": std,
                "coefficient_of_variation": coef_var,
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# 3B.3: Inter-rater dispersion (mean/std/range across strategies)
# ----------------------------------------------------------------------

def run_inter_rater_from_prompt_robustness() -> None:
    """
    3B.3: Simple 'inter-rater' style summary where each prompting strategy
    (zero_shot, cot, few_shot) is treated as a different rater assigning
    a 0–100 consistency score per event.
    """
    if not os.path.exists(PROMPT_ROBUST_OUT):
        print(f"[warn] {PROMPT_ROBUST_OUT} not found; skipping inter-rater summary")
        return

    with open(PROMPT_ROBUST_OUT, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    by_event: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        ev = r["event"]
        by_event.setdefault(
            ev,
            {
                "event": ev,
                "event_name": r.get("event_name", ev),
                "scores": {},
            },
        )
        by_event[ev]["scores"][r["strategy"]] = r["overall_consistency"]

    os.makedirs(os.path.dirname(INTER_RATER_OUT), exist_ok=True)
    with open(INTER_RATER_OUT, "w", encoding="utf-8") as f_out:
        for ev, rec in by_event.items():
            scores_dict = rec["scores"]
            scores_list = list(scores_dict.values())
            if not scores_list:
                continue

            mean_score = sum(scores_list) / len(scores_list)
            std = float(statistics.pstdev(scores_list)) if len(scores_list) > 1 else 0.0
            score_range = max(scores_list) - min(scores_list)

            out = {
                "event": ev,
                "event_name": rec["event_name"],
                "strategy_scores": scores_dict,
                "mean": mean_score,
                "std": std,
                "range": score_range,
            }
            f_out.write(json.dumps(out, ensure_ascii=False) + "\n")


# ----------------------------------------------------------------------
# 3B.4: Cohen's Kappa across strategies (categorical agreement)
# ----------------------------------------------------------------------

def categorize_score(score: int) -> str:
    """
    Map a 0–100 consistency score into a categorical label
    so we can compute Cohen's kappa.

    high   : score >= 80
    medium : 50 <= score < 80
    low    : score < 50
    """
    if score >= 80:
        return "high"
    elif score >= 50:
        return "medium"
    else:
        return "low"


def cohen_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    """
    Compute Cohen's kappa for two lists of categorical labels of equal length.

    κ = (P_o - P_e) / (1 - P_e)
    where:
      - P_o is observed agreement
      - P_e is expected agreement by chance
    """
    assert len(labels_a) == len(labels_b)
    n = len(labels_a)
    if n == 0:
        return 0.0

    # All possible categories
    categories = sorted(set(labels_a) | set(labels_b))
    if not categories:
        return 0.0

    # Observed agreement
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    p_o = agree / n

    # Category frequencies
    freq_a = {c: 0 for c in categories}
    freq_b = {c: 0 for c in categories}
    for a in labels_a:
        freq_a[a] += 1
    for b in labels_b:
        freq_b[b] += 1

    # Expected agreement
    p_e = 0.0
    for c in categories:
        p_e += (freq_a[c] / n) * (freq_b[c] / n)

    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e) if (1.0 - p_e) > 0 else 0.0


def compute_kappa_inter_rater() -> None:
    """
    Treat each prompting strategy (zero_shot, cot, few_shot)
    as a 'rater' assigning a categorical label (high/medium/low)
    to each event, then compute Cohen's kappa between each pair
    of raters across all events.

    Results are written to KAPPA_OUT as a single JSONL record.
    """
    if not os.path.exists(PROMPT_ROBUST_OUT):
        print(f"[warn] {PROMPT_ROBUST_OUT} not found; skipping kappa computation")
        return

    with open(PROMPT_ROBUST_OUT, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    # Group by event: {event: {"event_name": ..., "zero_shot": score, "cot": score, "few_shot": score}}
    by_event: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        ev = r["event"]
        by_event.setdefault(
            ev,
            {"event": ev, "event_name": r.get("event_name", ev), "scores": {}},
        )
        by_event[ev]["scores"][r["strategy"]] = r["overall_consistency"]

    events: List[str] = []
    labels_zero: List[str] = []
    labels_cot: List[str] = []
    labels_few: List[str] = []

    for ev, rec in by_event.items():
        scores = rec["scores"]
        # Only include events where we have all 3 strategies
        if not all(k in scores for k in ("zero_shot", "cot", "few_shot")):
            continue

        zs_cat = categorize_score(scores["zero_shot"])
        cot_cat = categorize_score(scores["cot"])
        few_cat = categorize_score(scores["few_shot"])

        events.append(ev)
        labels_zero.append(zs_cat)
        labels_cot.append(cot_cat)
        labels_few.append(few_cat)

    if not events:
        print("[warn] No events with all three strategies; skipping kappa.")
        return

    kappa_zero_vs_cot = cohen_kappa(labels_zero, labels_cot)
    kappa_zero_vs_few = cohen_kappa(labels_zero, labels_few)
    kappa_cot_vs_few = cohen_kappa(labels_cot, labels_few)

    os.makedirs(os.path.dirname(KAPPA_OUT), exist_ok=True)
    with open(KAPPA_OUT, "w", encoding="utf-8") as f_out:
        record = {
            "events": events,
            "category_labels": {
                "zero_shot": labels_zero,
                "cot": labels_cot,
                "few_shot": labels_few,
            },
            "kappa": {
                "zero_vs_cot": kappa_zero_vs_cot,
                "zero_vs_few": kappa_zero_vs_few,
                "cot_vs_few": kappa_cot_vs_few,
            },
        }
        f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[ok] Wrote Cohen's kappa inter-rater results to {KAPPA_OUT}")


# ----------------------------------------------------------------------
# Main entrypoint
# ----------------------------------------------------------------------

def main():
    if not os.path.exists(EVENT_CLAIMS_PATH):
        raise FileNotFoundError(f"{EVENT_CLAIMS_PATH} not found")

    records = load_event_claims(EVENT_CLAIMS_PATH)
    grouped = group_claims_by_event(records)

    print("[info] Running Prompt Robustness (3B.1)")
    run_prompt_robustness(grouped)

    print("[info] Running Self-Consistency (3B.2)")
    run_self_consistency(grouped)

    print("[info] Computing inter-rater dispersion across strategies (3B.3)")
    run_inter_rater_from_prompt_robustness()

    print("[info] Computing Cohen's kappa inter-rater agreement (3B.4)")
    compute_kappa_inter_rater()

    print(f"[ok] Wrote prompt robustness results to {PROMPT_ROBUST_OUT}")
    print(f"[ok] Wrote self-consistency results to {SELF_CONSIST_OUT}")
    print(f"[ok] Wrote inter-rater summary to {INTER_RATER_OUT}")
    print(f"[ok] Wrote kappa inter-rater summary to {KAPPA_OUT}")


if __name__ == "__main__":
    main()
