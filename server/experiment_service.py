"""Experiment workflow and server-side scoring."""
from typing import Any, Dict

from experiment_config import FINAL_STAGE_ORDER, STAGE_ORDER, build_participant_plan
from experiment_materials import load_materials
from database import DuplicateSubmissionError, ExperimentDatabase


OPAQUE_RENDER_MODES = {"TE": "layout_a", "CS": "layout_b", "SE": "layout_c", "BL": "layout_d"}


class ExperimentService:
    def __init__(self, db: ExperimentDatabase, materials=None):
        self.db = db
        self.materials = materials or load_materials()

    def start_or_resume(self, participant_id, client_instance_id, mode="formal"):
        plan = build_participant_plan(participant_id, self.materials)
        session = self.db.create_or_resume_session(participant_id, client_instance_id, mode, plan["articles"])
        return self.session_payload(session["session_id"])

    def session_payload(self, session_id):
        session = self.db.get_session(session_id)
        if not session: raise ValueError("session not found")
        plan = build_participant_plan(session["participant_id"], self.materials)
        articles = self.db.get_articles(session_id)
        by_order = {a["article_order"]: a for a in articles}
        view = plan["participant_view"]
        for article in view["articles"]:
            persisted = by_order[article["article_order"]]
            article["render_mode"] = OPAQUE_RENDER_MODES[persisted["condition"]]  # participant payload does not expose condition labels.
        return {"session": session, "articles": view["articles"], "progress": {"responses": self.db.list_responses(session_id)}}

    def participant_payload(self, session_id):
        payload = self.session_payload(session_id)
        session = payload["session"]
        payload["session"] = {
            "session_id": session["session_id"],
            "participant_id": session["participant_id"],
            "status": session["status"],
            "current_stage": session["current_stage"],
            "current_article_order": session["current_article_order"],
        }
        return payload

    def advance_stage(self, session_id, stage, article_order=0):
        if stage not in set(STAGE_ORDER) | set(FINAL_STAGE_ORDER):
            raise ValueError("unknown stage")
        if not isinstance(article_order, int) or not 0 <= article_order <= 4:
            raise ValueError("article_order must be between 0 and 4")
        self.db.update_progress(session_id, stage, article_order)
        return self.session_payload(session_id)

    def log_event(self, session_id, article_id, event_type, payload, occurred_at, event_id):
        self.db.log_event(session_id, article_id, event_type, payload, occurred_at, event_id)

    def record_reading_start(self, session_id, article_order, article_id, start_ms):
        self.db.update_progress(session_id, "reading", article_order)
        self.log_event(session_id, article_id, "reading_start", {"start_ms": start_ms, "article_order": article_order, "stage": "reading"}, start_ms, f"reading-start-{session_id}-{article_order}-{start_ms}")

    def finish_reading(self, session_id, article_order, article_id, end_ms, document_height, normalized_scroll_distance=None, comment_interaction_count=0, start_ms=None, scroll_event_count=None, total_scroll_distance_px=None, max_scroll_y=None, comment_counts=None):
        start_ms = start_ms or self._reading_start_from_events(session_id, article_id)
        metrics = self.scroll_metrics(session_id, article_id, stage="reading")
        if normalized_scroll_distance is None:
            normalized_scroll_distance = metrics["total_scroll_distance_px"] / float(document_height or 1)
        if scroll_event_count is None:
            scroll_event_count = metrics["scroll_event_count"]
        if total_scroll_distance_px is None:
            total_scroll_distance_px = metrics["total_scroll_distance_px"]
        if max_scroll_y is None:
            max_scroll_y = metrics["max_scroll_y"]
        self.db.update_reading(session_id, article_order, article_id, start_ms, end_ms, document_height, normalized_scroll_distance, comment_interaction_count, scroll_event_count, total_scroll_distance_px, max_scroll_y, comment_counts)
        self.db.update_progress(session_id, "cra", article_order)
        return self.db._one("SELECT * FROM article_sessions WHERE session_id = ? AND article_order = ?", (session_id, article_order))

    def _reading_start_from_events(self, session_id, article_id):
        row = self.db._one("SELECT payload_json FROM events WHERE session_id = ? AND article_id = ? AND event_type = 'reading_start' ORDER BY event_row_id LIMIT 1", (session_id, article_id))
        if not row: raise ValueError("reading start not found")
        import json
        return int(json.loads(row["payload_json"])["start_ms"])

    def scroll_metrics(self, session_id, article_id, stage=None):
        events = self.db.list_events(session_id)
        ys = []
        for event in events:
            if event["article_id"] != article_id or event["event_type"] != "scroll":
                continue
            if stage and event.get("stage") not in (None, stage):
                continue
            value = event["payload"].get("scroll_y")
            if value is not None:
                ys.append(float(value))
        return {
            "scroll_event_count": len(ys),
            "total_scroll_distance_px": sum(abs(curr - prev) for prev, curr in zip(ys, ys[1:])),
            "max_scroll_y": max(ys, default=0),
        }

    def calculate_scroll_distance(self, session_id, article_id, document_height):
        metrics = self.scroll_metrics(session_id, article_id, stage="reading")
        return metrics["total_scroll_distance_px"] / float(document_height or 1)

    def submit_response(self, session_id, article_order, article_id, question_type, question_id, selected_option, item_start_ms, submit_ms, option_click_count=1, option_change_count=0, scroll_event_count=0, total_scroll_distance_px=0, max_scroll_y=0):
        question = next((q for q in self.materials[article_id]["questions"][question_type] if q["id"] == question_id), None)
        if not question: raise ValueError("unknown question")
        if not isinstance(selected_option, str) or not selected_option.strip():
            raise ValueError("selected_option must be a non-empty string")
        option_keys = {option["key"] for option in question["options"]}
        if selected_option not in option_keys:
            raise ValueError("selected_option is invalid")
        correct = selected_option == question["answer"]
        return self.db.insert_response(session_id, article_order, article_id, question_type, question_id, selected_option, correct, item_start_ms, submit_ms, option_click_count, option_change_count, scroll_event_count, total_scroll_distance_px, max_scroll_y)

    def submit_workload(self, session_id, article_order, values):
        nasa_fields = (
            "mental_demand", "physical_demand", "temporal_demand",
            "performance", "effort", "frustration",
        )
        rating_fields = ("reading_continuity", "comment_accessibility")
        expected = set(nasa_fields + rating_fields)
        if set(values) != expected:
            raise ValueError("workload survey fields are incomplete")
        normalized = {}
        for field in nasa_fields:
            value = int(values[field])
            if not 1 <= value <= 7:
                raise ValueError(f"{field} must be between 1 and 7")
            normalized[field] = value
        for field in rating_fields:
            value = int(values[field])
            if not 1 <= value <= 7:
                raise ValueError(f"{field} must be between 1 and 7")
            normalized[field] = value
        self.db.insert_workload(session_id, article_order, normalized)
        self.db.update_progress(session_id, "preference" if article_order == 4 else "instruction", article_order)

    def submit_preference(self, session_id, ranking, preferred_condition, reason):
        if not isinstance(ranking, (list, tuple)) or len(ranking) != 4 or len(set(ranking)) != 4:
            raise ValueError("preference ranking must contain four unique items")
        if set(ranking) != {"TE", "CS", "SE", "BL"} or preferred_condition != ranking[0]:
            raise ValueError("preference ranking is invalid")
        if not str(reason).strip():
            raise ValueError("preference reason is required")
        self.db.insert_preference(session_id, ranking, preferred_condition, reason)
        self.db.update_progress(session_id, "interview", 4)

    def submit_interview(self, session_id, answers, started_at):
        if set(answers) != {"q1", "q2", "q3", "q4"} or any(not str(answers[key]).strip() for key in ("q1", "q2", "q3", "q4")):
            raise ValueError("all four interview answers are required")
        self.db.insert_interview(session_id, answers, started_at)
        return self.db.finish_session(session_id)
