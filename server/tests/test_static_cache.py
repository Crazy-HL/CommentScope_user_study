import os
import sys
import tempfile
from pathlib import Path

from tornado.testing import AsyncHTTPTestCase

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import ExperimentDatabase  # noqa: E402
from experiment_service import ExperimentService  # noqa: E402
from server import make_app  # noqa: E402


class StaticEntryPointCacheTest(AsyncHTTPTestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.dist_dir = Path(self.tempdir.name) / "dist"
        self.dist_dir.mkdir()
        (self.dist_dir / "index.html").write_text("<!doctype html><html><body>test</body></html>", encoding="utf-8")
        self.db = ExperimentDatabase(Path(self.tempdir.name) / "experiment.sqlite3")
        self.service = ExperimentService(self.db)
        self.previous_dist_path = os.environ.get("CLIENT_DIST_PATH")
        os.environ["CLIENT_DIST_PATH"] = str(self.dist_dir)
        super().setUp()

    def tearDown(self):
        self.db.close()
        if self.previous_dist_path is None:
            os.environ.pop("CLIENT_DIST_PATH", None)
        else:
            os.environ["CLIENT_DIST_PATH"] = self.previous_dist_path
        self.tempdir.cleanup()
        super().tearDown()

    def get_app(self):
        return make_app(self.db, self.service)

    def test_spa_entry_point_is_not_cached(self):
        response = self.fetch("/admin")
        assert response.code == 200
        assert response.headers["Cache-Control"] == "no-store"
