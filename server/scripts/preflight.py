"""Validate the experiment materials, allocation, schema, and data directory."""
import argparse
import os
import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from database import ExperimentDatabase  # noqa: E402
from experiment_config import PARTICIPANTS, build_participant_plan, validate_allocation  # noqa: E402
from experiment_materials import load_materials, validate_materials  # noqa: E402


def run_preflight(db_path=None, require_admin_token=False):
    errors = []
    materials = load_materials()
    errors.extend(validate_materials(materials))
    errors.extend(validate_allocation([build_participant_plan(pid, materials) for pid in PARTICIPANTS]))
    path = Path(db_path or os.environ.get("EXPERIMENT_DB_PATH", SERVER_ROOT / "data" / "experiment.sqlite3"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        probe = path.parent / ".preflight-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        db = ExperimentDatabase(path)
        tables = {row["name"] for row in db._many("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"sessions", "article_sessions", "events", "responses", "workload_surveys", "preferences", "interviews"}
        missing = required - tables
        if missing:
            errors.append(f"missing database tables: {sorted(missing)}")
        db.close()
    except Exception as exc:  # pragma: no cover - defensive operational diagnostic
        errors.append(f"database not writable: {exc}")
    if require_admin_token and not os.environ.get("RESEARCHER_ADMIN_TOKEN"):
        errors.append("RESEARCHER_ADMIN_TOKEN is not set")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=None)
    parser.add_argument("--require-admin-token", action="store_true")
    args = parser.parse_args()
    errors = run_preflight(args.db, args.require_admin_token)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("preflight passed")


if __name__ == "__main__":
    main()
