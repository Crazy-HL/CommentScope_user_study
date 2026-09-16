import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import ExperimentDatabase
from scripts.backup_database import backup_database
from scripts.preflight import run_preflight


def test_online_backup_can_restore_database(tmp_path):
    source = tmp_path / "source.sqlite3"
    target = tmp_path / "backup.sqlite3"
    db = ExperimentDatabase(source)
    db.start = None
    db.close()
    backup_database(source, target)
    connection = sqlite3.connect(target)
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()
    assert "sessions" in tables


def test_preflight_validates_materials_allocation_and_writable_directory(tmp_path):
    errors = run_preflight(tmp_path / "preflight.sqlite3")
    assert errors == []
