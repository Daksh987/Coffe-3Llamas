"""
Generate COFFE predictions for one model.

Reads prompts from `datasets/<benchmark>/prompts.json` (the dataset is the
authoritative source, not any existing example file) and writes predictions to
`examples/<benchmark>/<model-name>.json` in the format the COFFE pipeline
expects:

    { "<prompt>": [["<output_str>"], true], ... }

Defaults target Groq's OpenAI-compatible endpoint, but `--api-endpoint` and
`--api-key` let you swap providers. API key is read from $GROQ_API_KEY (or a
project-root .env file with `GROQ_API_KEY=...`) unless `--api-key` is passed.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_EVERY = 25
DEFAULT_ENDPOINT = "https://api.groq.com/openai/v1"
DEFAULT_API_KEY_ENV = "GROQ_API_KEY"
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # exponential: 2, 4, 8, 16, 32 seconds
TEMPERATURE = 0.0
MAX_TOKENS = 2048


def load_dotenv(path: Path = REPO_ROOT / ".env") -> None:
    """Minimal .env loader so we don't pull in python-dotenv as a dep."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)


def call_model(prompt: str, client: OpenAI, model_id: str) -> str:
    """Generate one completion. Retries on transient errors; returns "" if all retries exhausted."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            wait = RETRY_BASE_DELAY ** (attempt + 1)
            print(
                f"    API error (attempt {attempt + 1}/{MAX_RETRIES}): {type(e).__name__}: {e}; "
                f"sleeping {wait}s",
                file=sys.stderr,
            )
            time.sleep(wait)
    print(
        f"    WARNING: gave up after {MAX_RETRIES} retries; storing empty string",
        file=sys.stderr,
    )
    return ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate COFFE predictions for one model.")
    p.add_argument(
        "--benchmark",
        choices=["function", "file"],
        required=True,
        help="Which COFFE split to generate predictions for.",
    )
    p.add_argument(
        "--model-name",
        required=True,
        help="Name used for the output filename, e.g. 'Llama4_Maverick'.",
    )
    p.add_argument(
        "--model-id",
        default=None,
        help="Model identifier sent to the API (default: same as --model-name).",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help=f"API key (default: read from ${DEFAULT_API_KEY_ENV} or .env).",
    )
    p.add_argument(
        "--api-endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"OpenAI-compatible API base URL (default: {DEFAULT_ENDPOINT}).",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: examples/<benchmark>/).",
    )
    p.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        help="Cap the number of new prompts to send (for testing). Default: all.",
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


def resolve_api_key(cli_value: str | None) -> str:
    if cli_value:
        return cli_value
    load_dotenv()
    key = os.environ.get(DEFAULT_API_KEY_ENV)
    if not key:
        sys.exit(
            f"ERROR: no API key. Pass --api-key, set ${DEFAULT_API_KEY_ENV}, "
            f"or put `{DEFAULT_API_KEY_ENV}=...` in {REPO_ROOT / '.env'}"
        )
    return key


def main() -> int:
    args = parse_args()
    api_key = resolve_api_key(args.api_key)
    model_id = args.model_id or args.model_name

    client = OpenAI(api_key=api_key, base_url=args.api_endpoint)

    prompts = load_prompts(args.benchmark)
    print(f"Loaded {len(prompts)} prompts from datasets/{args.benchmark}/prompts.json")
    print(f"Endpoint: {args.api_endpoint}")
    print(f"Model ID: {model_id}")

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else REPO_ROOT / "examples" / args.benchmark
    )
    output_file = output_dir / f"{args.model_name}.json"

    results = load_existing(output_file)
    if results:
        print(f"Resuming - {len(results)} prompts already in {output_file}")

    new_count = 0
    for i, prompt in enumerate(prompts):
        if prompt in results:
            continue
        if args.max_prompts is not None and new_count >= args.max_prompts:
            print(f"Hit --max-prompts={args.max_prompts} cap; stopping.")
            break
        completion = call_model(prompt, client, model_id)
        results[prompt] = [[completion], True]
        new_count += 1
        print(f"  [{i + 1}/{len(prompts)}] generated ({len(completion)} chars)")
        if new_count % CHECKPOINT_EVERY == 0:
            save(output_file, results)
            print(f"  checkpoint saved")

    save(output_file, results)
    print(f"Done - wrote {len(results)} predictions to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
