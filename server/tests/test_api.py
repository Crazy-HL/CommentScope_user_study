import json
import os
import sys
import tempfile
from pathlib import Path

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import ExperimentDatabase  # noqa: E402
from experiment_service import ExperimentService  # noqa: E402
from server import make_app  # noqa: E402


class ExperimentApiTest(AsyncHTTPTestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "api.sqlite3"
        self.db = ExperimentDatabase(self.db_path)
        self.service = ExperimentService(self.db)
        os.environ["RESEARCHER_ADMIN_TOKEN"] = "test-token"
        super().setUp()

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()
        super().tearDown()

    def get_app(self):
        return make_app(self.db, self.service)

    def json_request(self, method, path, payload=None, headers=None):
        return self.fetch(path, method=method, body=json.dumps(payload or {}).encode(), headers=headers or {"Content-Type": "application/json"})

    def test_participant_start_payload_hides_answers_and_internal_metadata(self):
        response = self.json_request("POST", "/api/sessions", {"participant_id": "P01", "client_instance_id": "client-a", "mode": "pilot"})
        assert response.code == 201
        payload = json.loads(response.body)
        assert payload["session"]["participant_id"] == "P01"
        assert "client_instance_id" not in payload["session"]
        assert "group_id" not in payload
        serialized = json.dumps(payload, ensure_ascii=False)
        assert '"answer"' not in serialized
        assert "internal_anchor" not in serialized
        assert "condition_code" not in serialized

    def test_participant_list_marks_same_client_session_as_resumable(self):
        start = self.json_request("POST", "/api/sessions", {"participant_id": "P01", "client_instance_id": "client-a", "mode": "pilot"})
        assert start.code == 201

        same_client = json.loads(self.fetch("/api/participants?client_instance_id=client-a").body)
        same_p01 = next(item for item in same_client["participants"] if item["participant_id"] == "P01")
        assert same_p01 == {"participant_id": "P01", "available": True, "resumable": True}

        other_client = json.loads(self.fetch("/api/participants?client_instance_id=client-b").body)
        other_p01 = next(item for item in other_client["participants"] if item["participant_id"] == "P01")
        assert other_p01 == {"participant_id": "P01", "available": False, "resumable": False}

    def test_event_and_response_submit_are_immediate_and_duplicate_is_rejected(self):
        start = self.json_request("POST", "/api/sessions", {"participant_id": "P02", "client_instance_id": "client-a", "mode": "pilot"})
        sid = json.loads(start.body)["session"]["session_id"]
        event = self.json_request("POST", f"/api/sessions/{sid}/events", {"article_id": "A02", "event_type": "click", "payload": {"comment_index": 0}, "occurred_at": 1000, "event_id": "event-1"})
        assert event.code == 201
        response = self.json_request("POST", f"/api/sessions/{sid}/responses", {"article_order": 1, "article_id": "A02", "question_type": "cra", "question_id": "R1", "selected_option": "A", "item_start_ms": 1100, "submit_ms": 2100})
        assert response.code == 201
        assert json.loads(response.body)["correct"] is True
        duplicate = self.json_request("POST", f"/api/sessions/{sid}/responses", {"article_order": 1, "article_id": "A02", "question_type": "cra", "question_id": "R1", "selected_option": "B", "item_start_ms": 1100, "submit_ms": 3100})
        assert duplicate.code == 409

    def test_response_rejects_non_scalar_selected_option_without_server_error(self):
        start = self.json_request("POST", "/api/sessions", {"participant_id": "P14", "client_instance_id": "client-a", "mode": "pilot"})
        sid = json.loads(start.body)["session"]["session_id"]
        response = self.json_request("POST", f"/api/sessions/{sid}/responses", {
            "article_order": 1, "article_id": "A02", "question_type": "cra",
            "question_id": "R1", "selected_option": {"key": "A"},
            "item_start_ms": 1100, "submit_ms": 2100,
        })
        assert response.code == 400
        assert json.loads(response.body)["error"] == "invalid_request"

    def test_admin_login_me_and_logout_use_session_cookie(self):
        login = self.json_request("POST", "/api/admin/login", {"username": "admin", "password": "admin123"})
        assert login.code == 200
        payload = json.loads(login.body)
        assert payload == {"authenticated": True, "username": "admin"}
        assert "admin123" not in login.body.decode()
        cookie = login.headers.get("Set-Cookie")
        assert cookie and "comment_scope_admin_session=" in cookie

        session_headers = {"Cookie": cookie.split(";", 1)[0]}
        me = self.fetch("/api/admin/me", method="GET", headers=session_headers)
        assert me.code == 200
        assert json.loads(me.body) == {"authenticated": True, "username": "admin"}

        logout = self.fetch("/api/admin/logout", method="POST", body=b"{}", headers=session_headers)
        assert logout.code == 200
        assert json.loads(logout.body) == {"logged_out": True}

        denied = self.fetch("/api/admin/me", method="GET", headers={"Cookie": logout.headers.get("Set-Cookie", "").split(";", 1)[0]})
        assert denied.code == 401

    def test_admin_login_rejects_invalid_credentials(self):
        login = self.json_request("POST", "/api/admin/login", {"username": "admin", "password": "wrong"})
        assert login.code == 401
        assert json.loads(login.body) == {"error": "invalid_credentials"}

    def test_admin_statistics_require_auth_and_return_empty_dashboard_shape(self):
        denied = self.fetch("/api/admin/summary", method="GET")
        assert denied.code == 401

        login = self.json_request("POST", "/api/admin/login", {"username": "admin", "password": "admin123"})
        cookie = login.headers["Set-Cookie"].split(";", 1)[0]
        headers = {"Cookie": cookie}
        summary = self.fetch("/api/admin/summary", method="GET", headers=headers)
        assert summary.code == 200
        payload = json.loads(summary.body)
        assert payload["overview"]["expected_participants"] == 24
        assert payload["metrics"]["CTIA"]["TE"]["n"] == 0

        analysis = self.fetch("/api/admin/analysis", method="GET", headers=headers)
        quality = self.fetch("/api/admin/data-quality", method="GET", headers=headers)
        assert analysis.code == 200
        assert quality.code == 200
        assert isinstance(json.loads(analysis.body)["statements"], list)
        assert isinstance(json.loads(quality.body)["issues"], list)

    def test_admin_statistics_reject_invalid_filter_values(self):
        headers = {"Authorization": "Bearer test-token"}
        response = self.fetch("/api/admin/summary?condition=unknown", method="GET", headers=headers)
        assert response.code == 400
        assert json.loads(response.body)["error"] == "invalid_request"

    def test_admin_summary_article_sequence_filters_participant_overview(self):
        headers = {"Authorization": "Bearer test-token"}
        response = self.fetch(
            "/api/admin/summary?article_sequence=02-03-04-01",
            method="GET",
            headers=headers,
        )

        assert response.code == 200
        payload = json.loads(response.body)
        assert [row["participant_id"] for row in payload["participant_overview"]] == [
            "P07", "P08", "P09", "P10", "P11", "P12"
        ]

    def test_admin_export_requires_token_and_reset_is_protected(self):
        denied = self.fetch("/api/admin/export", method="GET")
        assert denied.code == 401
        headers = {"Authorization": "Bearer test-token"}
        allowed = self.fetch("/api/admin/export?mode=formal", method="GET", headers=headers)
        assert allowed.code == 200
        assert "participant_id" in allowed.body.decode()
        reset = self.fetch("/api/admin/reset/P03", method="POST", body=b"{}", headers={**headers, "Content-Type": "application/json"})
        assert reset.code == 200

    def test_invalid_participant_and_stage_are_rejected(self):
        invalid = self.json_request("POST", "/api/sessions", {"participant_id": "P99", "client_instance_id": "client-a"})
        assert invalid.code == 400
        start = self.json_request("POST", "/api/sessions", {"participant_id": "P09", "client_instance_id": "client-a", "mode": "pilot"})
        sid = json.loads(start.body)["session"]["session_id"]
        invalid_stage = self.json_request("POST", f"/api/sessions/{sid}", {"stage": "not-a-stage", "article_order": 0})
        assert invalid_stage.code == 400

    def test_admin_export_can_return_json(self):
        headers = {"Authorization": "Bearer test-token"}
        allowed = self.fetch("/api/admin/export?mode=all&format=json", method="GET", headers=headers)
        assert allowed.code == 200
        assert allowed.headers["Content-Type"].startswith("application/json")
        payload = json.loads(allowed.body)
        assert isinstance(payload, list)

    def test_participant_render_mode_is_opaque(self):
        response = self.json_request("POST", "/api/sessions", {"participant_id": "P12", "client_instance_id": "client-a", "mode": "pilot"})
        assert response.code == 201
        payload = json.loads(response.body)
        modes = {article["render_mode"] for article in payload["articles"]}
        assert modes <= {"layout_a", "layout_b", "layout_c", "layout_d"}
        assert not any(article["render_mode"] in {"te", "cs", "se", "bl"} for article in payload["articles"])

    def test_admin_event_export_supports_csv_and_json_and_rejects_unknown_dataset(self):
        headers = {"Authorization": "Bearer test-token"}
        start = self.json_request("POST", "/api/sessions", {
            "participant_id": "P18", "client_instance_id": "client-events", "mode": "formal",
        })
        sid = json.loads(start.body)["session"]["session_id"]
        event = self.json_request("POST", f"/api/sessions/{sid}/events", {
            "article_id": "A02", "article_order": 1, "stage": "reading",
            "event_type": "comment_click", "payload": {"comment_id": "C01"},
            "occurred_at": 1000, "event_id": "api-export-event",
        })
        assert event.code == 201

        csv_response = self.fetch(
            "/api/admin/export?mode=all&dataset=events&format=csv",
            method="GET", headers=headers,
        )
        assert csv_response.code == 200
        assert csv_response.headers["Content-Type"].startswith("text/csv")
        assert "event_id" in csv_response.body.decode()
        assert "api-export-event" in csv_response.body.decode()

        json_response = self.fetch(
            "/api/admin/export?mode=all&dataset=events&format=json",
            method="GET", headers=headers,
        )
        assert json_response.code == 200
        payload = json.loads(json_response.body)
        assert any(item["event_id"] == "api-export-event" for item in payload)

        denied = self.fetch("/api/admin/export?dataset=events&format=csv", method="GET")
        assert denied.code == 401
        invalid = self.fetch(
            "/api/admin/export?dataset=unknown&format=csv",
            method="GET", headers=headers,
        )
        assert invalid.code == 400
        assert json.loads(invalid.body)["error"] == "invalid_dataset"
