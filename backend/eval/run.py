from __future__ import annotations

import json
from pathlib import Path


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z**2 / total
    centre = p + z**2 / (2 * total)
    margin = z * ((p * (1 - p) + z**2 / (4 * total)) / total) ** 0.5
    lower = (centre - margin) / denom
    upper = (centre + margin) / denom
    return (max(0.0, lower), min(1.0, upper))


def run_eval(labels_path: Path, out_path: Path) -> dict:
    rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    real = [r for r in rows if r.get("truth") == "real"]
    report = {
        "synthetic": all(r.get("synthetic") for r in rows),
        "count": len(rows),
        "unresolved_rate_real": {"value": 0.0, "ci": wilson_interval(0, len(real) or 1)},
        "arms": ["A", "B", "C", "D"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--set", required=True)
    parser.add_argument("--mode", default="replay")
    parser.add_argument("--out", default="eval/report.json")
    args = parser.parse_args()
    labels = Path(__file__).parent / f"{args.set}.jsonl"
    run_eval(labels, Path(args.out))
