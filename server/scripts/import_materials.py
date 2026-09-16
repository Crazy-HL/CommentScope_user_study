"""Validate and optionally copy the researcher-authored material snapshot."""
import argparse
import json
import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from experiment_materials import load_materials, validate_materials  # noqa: E402


def import_materials(source=None, destination=None):
    source = Path(source) if source else SERVER_ROOT / "materials.json"
    with source.open("r", encoding="utf-8") as handle:
        materials = json.load(handle)
    errors = validate_materials(materials)
    if errors:
        raise ValueError("; ".join(errors))
    if destination:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(materials, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return materials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(SERVER_ROOT / "materials.json"))
    parser.add_argument("--destination")
    args = parser.parse_args()
    materials = import_materials(args.source, args.destination)
    print(f"validated {len(materials)} articles and {sum(len(item['comments']) for item in materials.values())} comments")


if __name__ == "__main__":
    main()
