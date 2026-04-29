"""
Pre-flight coverage validator for COFFE prediction files.

Compares a prediction file's keys against `datasets/<benchmark>/prompts.json`
(398 prompts for `function`, 358 for `file`). Run this BEFORE invoking
`coffe pipe` so a missing-key run does not silently waste hours of pipeline time.

Exit codes:
    0  every dataset prompt has a prediction (extras are warned about, not failed)
    1  one or more dataset prompts are missing from the prediction file, or the
       prediction file itself is missing/malformed

Honors story #10's "no pipeline code changes" constraint by living in scripts/
instead of modifying coffe/main.py.
"""
import argparse
import json
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PREVIEW_LIMIT = 10
PREVIEW_CHARS = 80


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate a COFFE prediction file's prompt coverage.")
    p.add_argument(
        "--benchmark",
        choices=["function", "file"],
        required=True,
        help="Which COFFE split the prediction file targets.",
    )
    p.add_argument(
        "--prediction-file",
        required=True,
        type=Path,
        help="Path to the prediction JSON file to validate.",
    )
    return p.parse_args()


def load_dataset_prompts(benchmark: str) -> set[str]:
    path = REPO_ROOT / "datasets" / benchmark / "prompts.json"
    if not path.exists():
        sys.exit(f"ERROR: dataset prompt file not found at {path}")
    prompts = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(prompts, list):
        sys.exit(f"ERROR: expected a JSON list at {path}, got {type(prompts).__name__}")
    return set(prompts)


def load_prediction_keys(prediction_file: Path) -> set[str]:
    if not prediction_file.exists():
        sys.exit(f"ERROR: prediction file not found at {prediction_file}")
    try:
        data = json.loads(prediction_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: prediction file is not valid JSON: {e}")
    if not isinstance(data, dict):
        sys.exit(
            f"ERROR: expected a JSON object (dict) at {prediction_file}, "
            f"got {type(data).__name__}"
        )
    return set(data.keys())


def preview_prompts(prompts: set[str], limit: int = PREVIEW_LIMIT) -> str:
    sample = sorted(prompts)[:limit]
    lines = []
    for p in sample:
        first_line = p.splitlines()[0] if p else ""
        truncated = (first_line[:PREVIEW_CHARS] + "...") if len(first_line) > PREVIEW_CHARS else first_line
        lines.append(f"  - {truncated}")
    if len(prompts) > limit:
        lines.append(f"  ... and {len(prompts) - limit} more")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    start = time.perf_counter()

    dataset_prompts = load_dataset_prompts(args.benchmark)
    prediction_keys = load_prediction_keys(args.prediction_file)

    missing = dataset_prompts - prediction_keys
    extra = prediction_keys - dataset_prompts

    print(f"Benchmark:         {args.benchmark}")
    print(f"Prediction file:   {args.prediction_file}")
    print(f"Dataset prompts:   {len(dataset_prompts)}")
    print(f"Prediction keys:   {len(prediction_keys)}")
    print(f"Missing (dataset only):  {len(missing)}")
    print(f"Extra (prediction only): {len(extra)}")

    elapsed = time.perf_counter() - start
    print(f"Validated in {elapsed:.2f}s")
    print()

    if missing:
        print(f"FAIL: {len(missing)} dataset prompt(s) are not covered by the prediction file.")
        print("First missing prompts (truncated):")
        print(preview_prompts(missing))
        return 1

    if extra:
        print(f"WARNING: {len(extra)} prediction key(s) do not match any dataset prompt.")
        print("These will be silently ignored by the pipeline. First extras (truncated):")
        print(preview_prompts(extra))
        print()

    print("OK: every dataset prompt has a prediction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
