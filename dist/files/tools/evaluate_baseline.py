#!/usr/bin/env python3
"""Teaching-only deterministic baseline. No model, network or real applications.

Strict accepted grammar is intentional: this is a baseline and product boundary
exercise, not a universal parser. Published holdout examples are NOT a sealed
benchmark; create a new independent held-out set for a real evaluation.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"Deadline: (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) ([A-Za-z_]+/[A-Za-z_]+)")

def extract(text):
    match = PATTERN.fullmatch(text.strip())
    if not match:
        return {"status": "review"}
    date, time, zone = match.groups()
    try:
        local = datetime.fromisoformat(date + "T" + time)
        tz = ZoneInfo(zone)
        # Both folds must agree and round-trip: no guessing ambiguous DST times.
        first, second = local.replace(tzinfo=tz, fold=0), local.replace(tzinfo=tz, fold=1)
        if first.utcoffset() != second.utcoffset():
            return {"status": "review"}
        if first.astimezone(ZoneInfo("UTC")).astimezone(tz).replace(tzinfo=None) != local:
            return {"status": "review"}
    except (ValueError, ZoneInfoNotFoundError):
        return {"status": "review"}
    return {"status": "candidate", "local": date + "T" + time, "zone": zone}

def main():
    cases = json.loads((ROOT / "research/ai-eval-cases.json").read_text())
    rows = []
    for case in cases:
        actual = extract(case["text"])
        rows.append({"id": case["id"], "split": case["split"], "expected":case["expected"], "actual":actual, "matches_expected":actual == case["expected"]})
    report = {
        "nature":"12 authored synthetic software checks; not a live-model benchmark or user-study result",
        "checked":"2026-11-13",
        "rule":"strict exact format; candidate always requires human source review",
        "sealed_holdout":False,
        "passed":sum(r["matches_expected"] for r in rows),
        "total":len(rows),
        "model_evaluation":"not_performed",
        "business_outcomes":"not_measured",
        "rows":rows,
    }
    out = ROOT / "verification/ai-baseline.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ["passed","total","model_evaluation"]}))
    return 0 if report["passed"] == report["total"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
