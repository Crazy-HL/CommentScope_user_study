"""Tornado application for the CommentScope participant experiment."""
import json
import os
from pathlib import Path

import tornado.web

from admin_auth import AdminAuth
from admin_stats import AdminStats
from database import DuplicateSubmissionError, ExperimentDatabase, ParticipantCompletedError, ParticipantLockedError
from experiment_service import ExperimentService


class JsonHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", os.environ.get("CORS_ORIGIN", "*"))
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.set_header("Cache-Control", "no-store")

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()

    def body_json(self):
        if not self.request.body:
            return {}
        try:
            return json.loads(self.request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise tornado.web.HTTPError(400, reason="Invalid JSON")

    def respond(self, payload, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.finish(json.dumps(payload, ensure_ascii=False))

    def handle_error(self, error):
        if isinstance(error, ParticipantLockedError):
            self.respond({"error": "participant_locked", "message": "该参与者编号正在另一个浏览器中使用。"}, 409)
        elif isinstance(error, ParticipantCompletedError):
            self.respond({"error": "participant_completed", "message": "该参与者编号的正式实验已经完成。"}, 409)
        elif isinstance(error, DuplicateSubmissionError):
            self.respond({"error": "duplicate_submission", "message": "该题目已经提交，不能修改。"}, 409)
        elif isinstance(error, ValueError):
            self.respond({"error": "invalid_request", "message": str(error)}, 400)
        else:
            raise error


class ParticipantsHandler(JsonHandler):
    def initialize(self, db):
        self.db = db

    def get(self):
        from experiment_config import PARTICIPANTS
        client_instance_id = self.get_query_argument("client_instance_id", "").strip()
        active_sessions = self.db._many(
            "SELECT participant_id, client_instance_id FROM sessions WHERE status = 'active'"
        )
        active_by_participant = {
            row["participant_id"]: row["client_instance_id"]
            for row in active_sessions
        }
        self.respond({
            "participants": [
                {
                    "participant_id": pid,
                    "available": pid not in active_by_participant or active_by_participant[pid] == client_instance_id,
                    "resumable": pid in active_by_participant and active_by_participant[pid] == client_instance_id,
                }
                for pid in PARTICIPANTS
            ]
        })


class SessionHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self):
        data = self.body_json()
        participant_id = str(data.get("participant_id", "")).strip()
        client_id = str(data.get("client_instance_id", "")).strip()
        if not participant_id or not client_id:
            self.respond({"error": "participant_id and client_instance_id are required"}, 400)
            return
        try:
            existing = self.service.db.get_active_session_for_participant(participant_id)
            payload = self.service.start_or_resume(participant_id, client_id)
            self.respond(self.service.participant_payload(payload["session"]["session_id"]), 200 if existing else 201)
        except (ParticipantLockedError, ParticipantCompletedError, DuplicateSubmissionError, ValueError) as exc:
            self.handle_error(exc)


class SessionDetailHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def get(self, session_id):
        try:
            self.respond(self.service.participant_payload(session_id))
        except ValueError as exc:
            self.handle_error(exc)

    def post(self, session_id):
        data = self.body_json()
        try:
            self.service.advance_stage(session_id, str(data["stage"]), int(data.get("article_order", 0)))
            self.respond(self.service.participant_payload(session_id))
        except (ValueError, KeyError) as exc:
            self.handle_error(ValueError(str(exc)))


class EventHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        required = ("event_type", "event_id", "occurred_at")
        if any(key not in data for key in required):
            self.respond({"error": "event_type, event_id and occurred_at are required"}, 400)
            return
        try:
            self.service.log_event(session_id, data.get("article_id"), data["event_type"], data.get("payload", {}), data["occurred_at"], data["event_id"])
            self.respond({"saved": True}, 201)
        except ValueError as exc:
            self.handle_error(exc)


class ReadingHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        try:
            reading = self.service.finish_reading(
                session_id, int(data["article_order"]), data["article_id"], int(data["reading_end_ms"]),
                float(data["document_height"]), data.get("normalized_scroll_distance"),
                int(data.get("comment_interaction_count", 0)), data.get("reading_start_ms"),
                data.get("scroll_event_count"), data.get("total_scroll_distance_px"),
                data.get("max_scroll_y"), data.get("comment_counts"),
            )
            self.respond({"reading": reading, "next_stage": "cra"}, 201)
        except (ValueError, KeyError, TypeError) as exc:
            self.handle_error(ValueError(str(exc)))


class ResponseHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        try:
            response = self.service.submit_response(
                session_id, int(data["article_order"]), data["article_id"], data["question_type"],
                data["question_id"], data["selected_option"], int(data["item_start_ms"]),
                int(data["submit_ms"]), int(data.get("option_click_count", 1)),
                int(data.get("option_change_count", 0)), data.get("scroll_event_count"),
                data.get("total_scroll_distance_px"), data.get("max_scroll_y"),
            )
            self.respond({"question_id": response["question_id"], "correct": bool(response["correct"]), "elapsed_ms": response["elapsed_ms"]}, 201)
        except (DuplicateSubmissionError, ValueError, KeyError, TypeError) as exc:
            self.handle_error(exc)


class WorkloadHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        try:
            self.service.submit_workload(session_id, int(data["article_order"]), data["values"])
            self.respond({"saved": True}, 201)
        except (DuplicateSubmissionError, ValueError, KeyError, TypeError) as exc:
            self.handle_error(exc)


class PreferenceHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        try:
            self.service.submit_preference(session_id, data["ranking"], data["preferred_condition"], data.get("reason", ""))
            self.respond({"saved": True}, 201)
        except (DuplicateSubmissionError, ValueError, KeyError, TypeError) as exc:
            self.handle_error(exc)


class InterviewHandler(JsonHandler):
    def initialize(self, service):
        self.service = service

    def post(self, session_id):
        data = self.body_json()
        try:
            session = self.service.submit_interview(session_id, data["answers"], data["started_at"])
            self.respond({"saved": True, "completed": session["status"] == "completed"}, 201)
        except (DuplicateSubmissionError, ValueError, KeyError, TypeError) as exc:
            self.handle_error(exc)


class AdminLoginHandler(JsonHandler):
    def initialize(self, auth):
        self.auth = auth

    def post(self):
        data = self.body_json()
        username = str(data.get("username", ""))
        password = str(data.get("password", ""))
        if not self.auth.verify_credentials(username, password):
            self.respond({"error": "invalid_credentials"}, 401)
            return
        configured_username, _ = self.auth.credentials()
        self.auth.set_session(self, configured_username)
        self.respond({"authenticated": True, "username": configured_username})


class AdminMeHandler(JsonHandler):
    def initialize(self, auth):
        self.auth = auth

    def get(self):
        username = self.auth.session_username(self)
        if username is None:
            configured = os.environ.get("RESEARCHER_ADMIN_TOKEN", "")
            supplied = self.request.headers.get("Authorization", "")
            if configured and supplied == f"Bearer {configured}":
                username = self.auth.credentials()[0]
        if username is None:
            self.respond({"error": "unauthorized"}, 401)
            return
        self.respond({"authenticated": True, "username": username})


class AdminLogoutHandler(JsonHandler):
    def initialize(self, auth):
        self.auth = auth

    def post(self):
        self.auth.clear_session(self)
        self.respond({"logged_out": True})


class AdminHandler(JsonHandler):
    def initialize(self, db, auth):
        self.db = db
        self.auth = auth

    def admin_filters(self):
        return {
            key: self.get_query_argument(key, "").strip()
            for key in ("participant_id", "article_id", "condition", "status", "article_order", "article_sequence")
        }

    def check_auth(self):
        if self.auth.is_authenticated(self):
            return True
        configured = os.environ.get("RESEARCHER_ADMIN_TOKEN", "")
        supplied = self.request.headers.get("Authorization", "")
        if configured and supplied == f"Bearer {configured}":
            return True
        self.respond({"error": "unauthorized"}, 401)
        return False


class AdminSummaryHandler(AdminHandler):
    def get(self):
        if not self.check_auth():
            return
        try:
            self.respond(AdminStats(self.db).summary(self.admin_filters()))
        except ValueError as exc:
            self.handle_error(exc)


class AdminAnalysisHandler(AdminHandler):
    def get(self):
        if not self.check_auth():
            return
        try:
            self.respond(AdminStats(self.db).analysis(self.admin_filters()))
        except ValueError as exc:
            self.handle_error(exc)


class AdminDataQualityHandler(AdminHandler):
    def get(self):
        if not self.check_auth():
            return
        try:
            self.respond(AdminStats(self.db).data_quality(self.admin_filters()))
        except ValueError as exc:
            self.handle_error(exc)


class AdminExportHandler(AdminHandler):
    def get(self):
        if not self.check_auth(): return
        mode = self.get_query_argument("mode", "formal")
        if mode not in {"formal", "pilot", "all"}:
            self.respond({"error": "invalid mode"}, 400); return
        selected_mode = None if mode == "all" else mode
        dataset = self.get_query_argument("dataset", "analysis").lower()
        if dataset not in {"analysis", "events"}:
            self.respond({"error": "invalid_dataset"}, 400)
            return
        export_format = self.get_query_argument("format", "csv").lower()
        if export_format == "json":
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.set_header("Content-Disposition", f'attachment; filename="comment-scope-{dataset}-{mode}.json"')
            rows = self.db.export_event_rows(selected_mode) if dataset == "events" else self.db.export_rows(selected_mode)
            self.finish(json.dumps(rows, ensure_ascii=False))
            return
        if export_format != "csv":
            self.respond({"error": "invalid format"}, 400)
            return
        self.set_header("Content-Type", "text/csv; charset=utf-8")
        self.set_header("Content-Disposition", f'attachment; filename="comment-scope-{dataset}-{mode}.csv"')
        self.finish(self.db.export_events_csv(selected_mode) if dataset == "events" else self.db.export_csv(selected_mode))


class AdminResetHandler(AdminHandler):
    def post(self, participant_id):
        if not self.check_auth(): return
        self.db.reset_participant(participant_id)
        self.respond({"reset": True, "participant_id": participant_id})


class AdminStatusHandler(AdminHandler):
    def get(self):
        if not self.check_auth(): return
        sessions = self.db._many("SELECT participant_id, mode, status, current_stage, current_article_order, last_seen_at FROM sessions ORDER BY participant_id, started_at")
        self.respond({"sessions": sessions})


class SpaStaticHandler(tornado.web.StaticFileHandler):
    def get(self, path, include_body=True):
        requested = self.parse_url_path(path)
        root = Path(self.root)
        candidate = root / requested
        if not requested or not candidate.is_file():
            # The entry point contains hashed JS/CSS filenames. Caching it can
            # leave a browser requesting bundles from a previous build; those
            # requests are then SPA-fallback HTML and the app becomes blank.
            path = "index.html"
        return super().get(path, include_body=include_body)

    def set_extra_headers(self, path):
        if Path(path).name == "index.html":
            # StaticFileHandler applies its own long-lived cache policy after
            # get() starts, so set the entry-point policy at its extension hook.
            self.set_header("Cache-Control", "no-store")
            self.set_header("Pragma", "no-cache")
            self.set_header("Expires", "0")
            return
        super().set_extra_headers(path)


def make_app(db=None, service=None):
    db = db or ExperimentDatabase()
    service = service or ExperimentService(db)
    auth = AdminAuth()
    handlers = [
        (r"/api/participants", ParticipantsHandler, {"db": db}),
        (r"/api/sessions", SessionHandler, {"service": service}),
        (r"/api/sessions/([^/]+)", SessionDetailHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/events", EventHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/reading", ReadingHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/responses", ResponseHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/workload", WorkloadHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/preference", PreferenceHandler, {"service": service}),
        (r"/api/sessions/([^/]+)/interview", InterviewHandler, {"service": service}),
        (r"/api/admin/login", AdminLoginHandler, {"auth": auth}),
        (r"/api/admin/me", AdminMeHandler, {"auth": auth}),
        (r"/api/admin/logout", AdminLogoutHandler, {"auth": auth}),
        (r"/api/admin/summary", AdminSummaryHandler, {"db": db, "auth": auth}),
        (r"/api/admin/analysis", AdminAnalysisHandler, {"db": db, "auth": auth}),
        (r"/api/admin/data-quality", AdminDataQualityHandler, {"db": db, "auth": auth}),
        (r"/api/admin/export", AdminExportHandler, {"db": db, "auth": auth}),
        (r"/api/admin/status", AdminStatusHandler, {"db": db, "auth": auth}),
        (r"/api/admin/reset/([^/]+)", AdminResetHandler, {"db": db, "auth": auth}),
    ]
    dist_path = os.environ.get("CLIENT_DIST_PATH", str(Path(__file__).resolve().parents[1] / "client" / "dist"))
    if Path(dist_path).is_dir():
        handlers.append((r"/(.*)", SpaStaticHandler, {"path": dist_path}))
    return tornado.web.Application(handlers, debug=False, cookie_secret=auth.session_secret())


if __name__ == "__main__":
    import tornado.ioloop
    port = int(os.environ.get("PORT", "8888"))
    app = make_app()
    app.listen(port)
    print(f"CommentScope experiment server listening on http://0.0.0.0:{port}")
    tornado.ioloop.IOLoop.current().start()
