# src/part1_data/validate_loc_improved.py

import json

PATH = "data/processed/loc_lincoln_improved.jsonl"

REQUIRED_KEYS = [
    "id",
    "title",
    "reference",
    "document_type",
    "date",
    "place",
    "from",
    "to",
    "content",
]

def main():
    total = 0
    non_empty = {k: 0 for k in REQUIRED_KEYS}

    with open(PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            total += 1

            # Check required keys
            missing = [k for k in REQUIRED_KEYS if k not in rec]
            if missing:
                print(f"[ERROR] Record {rec.get('id')} missing keys: {missing}")

            # Count non-empty values
            for k in REQUIRED_KEYS:
                v = rec.get(k, "")
                if isinstance(v, str) and v.strip():
                    non_empty[k] += 1

    print(f"\n[OK] Loaded {total} records from {PATH}")
    print("\n[non-empty field counts]")
    for k, v in non_empty.items():
        print(f"  {k}: {v}/{total}")

if __name__ == "__main__":
    main()
