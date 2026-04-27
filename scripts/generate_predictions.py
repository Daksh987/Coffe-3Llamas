"""
Generate COFFE predictions for one model.

Reads prompts from `datasets/<benchmark>/prompts.json` (the dataset is the
authoritative source, not any existing example file) and writes predictions to
`examples/<benchmark>/<model-name>.json` in the format the COFFE pipeline
expects:

    { "<prompt>": [["<output_str>"], true], ... }

Issue #11 scaffolding: this version writes empty stub completions so the
output schema, file layout, CLI, and resumability can be validated without
spending API budget. Issue #12 replaces `call_model()` with real API calls.
"""
import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_EVERY = 50


def call_model(prompt: str, model_name: str) -> str:
    """Generate one completion for one prompt. Stub for #11; real API in #12."""
    return ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate COFFE predictions for one model.",
    )
    p.add_argument(
        "--benchmark",
        choices=["function", "file"],
        required=True,
        help="Which COFFE split to generate predictions for.",
    )
    p.add_argument(
        "--model-name",
        required=True,
        help="Model name used for the output filename, e.g. 'Llama4_Maverick'.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: examples/<benchmark>/).",
    )
    return p.parse_args()


def load_prompts(benchmark: str) -> list[str]:
    path = REPO_ROOT / "datasets" / benchmark / "prompts.json"
    if not path.exists():
        sys.exit(f"ERROR: prompt file not found at {path}")
    prompts = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(prompts, list):
        sys.exit(f"ERROR: expected a JSON list at {path}, got {type(prompts).__name__}")
    return prompts


def load_existing(output_file: Path) -> dict:
    if not output_file.exists():
        return {}
    try:
        return json.loads(output_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: existing output file at {output_file} is not valid JSON: {e}")


def save(output_file: Path, results: dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()

    prompts = load_prompts(args.benchmark)
    print(f"Loaded {len(prompts)} prompts from datasets/{args.benchmark}/prompts.json")

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else REPO_ROOT / "examples" / args.benchmark
    )
    output_file = output_dir / f"{args.model_name}.json"

    results = load_existing(output_file)
    if results:
        print(f"Resuming — {len(results)} prompts already in {output_file}")

    new_count = 0
    for i, prompt in enumerate(prompts):
        if prompt in results:
            continue
        completion = call_model(prompt, args.model_name)
        results[prompt] = [[completion], True]
        new_count += 1
        if new_count % CHECKPOINT_EVERY == 0:
            save(output_file, results)
            print(f"  [{i + 1}/{len(prompts)}] checkpoint saved")

    save(output_file, results)
    print(f"Done — wrote {len(results)} predictions to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
