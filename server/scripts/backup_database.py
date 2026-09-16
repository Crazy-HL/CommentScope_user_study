"""Create a consistent online backup of the live SQLite database."""
import argparse
import sqlite3
from pathlib import Path


def backup_database(source, destination):
    source = Path(source)
    destination = Path(destination)
    if not source.exists():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    source_connection = sqlite3.connect(str(source), timeout=30)
    target_connection = sqlite3.connect(str(destination), timeout=30)
    try:
        source_connection.backup(target_connection)
        target_connection.commit()
    finally:
        target_connection.close()
        source_connection.close()
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default=None, help="live SQLite path")
    parser.add_argument("destination", nargs="?", default=None, help="backup SQLite path")
    args = parser.parse_args()
    import os
    source = args.source or os.environ.get("EXPERIMENT_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "experiment.sqlite3"))
    destination = args.destination or f"{source}.bak"
    print(backup_database(source, destination))


if __name__ == "__main__":
    main()
