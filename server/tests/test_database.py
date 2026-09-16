import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import ExperimentDatabase, DuplicateSubmissionError, ParticipantLockedError  # noqa: E402
from experiment_service import ExperimentService  # noqa: E402


def make_service(tmp_path):
    db = ExperimentDatabase(tmp_path / "experiment.sqlite3")
    return db, ExperimentService(db)


def test_session_is_persistent_and_same_client_can_resume(tmp_path):
    db, service = make_service(tmp_path)
    session = service.start_or_resume("P01", "client-a", mode="pilot")
    service.advance_stage(session["session"]["session_id"], "instruction")
    db.close()

    reopened = ExperimentDatabase(tmp_path / "experiment.sqlite3")
    resumed = ExperimentService(reopened).start_or_resume("P01", "client-a", mode="pilot")
    assert resumed["session"]["session_id"] == session["session"]["session_id"]
    assert resumed["session"]["current_stage"] == "instruction"
    reopened.close()


def test_participant_cannot_be_used_by_another_active_client(tmp_path):
    db, service = make_service(tmp_path)
    service.start_or_resume("P02", "client-a", mode="formal")
    with pytest.raises(ParticipantLockedError):
        service.start_or_resume("P02", "client-b", mode="formal")
    db.close()


def test_response_is_scored_server_side_and_cannot_be_changed(tmp_path):
    db, service = make_service(tmp_path)
    session = service.start_or_resume("P03", "client-a", mode="pilot")
    service.advance_stage(session["session"]["session_id"], "reading")
    service.record_reading_start(session["session"]["session_id"], 1, "A02", 1700000000000)
    result = service.submit_response(
        session["session"]["session_id"], 1, "A02", "cra", "R1", "A", 1700000001000, 1700000004000
    )
    assert bool(result["correct"]) is True
    assert result["elapsed_ms"] == 3000
    with pytest.raises(DuplicateSubmissionError):
        service.submit_response(
            session["session"]["session_id"], 1, "A02", "cra", "R1", "B", 1700000001000, 1700000005000
        )
    db.close()


def test_scroll_distance_and_event_are_saved(tmp_path):
    db, service = make_service(tmp_path)
    session = service.start_or_resume("P04", "client-a", mode="pilot")
    service.record_reading_start(session["session"]["session_id"], 1, "A02", 1000)
    service.log_event(session["session"]["session_id"], "A02", "scroll", {"scroll_y": 0}, 1000, "e1")
    service.log_event(session["session"]["session_id"], "A02", "scroll", {"scroll_y": 300}, 1100, "e2")
    service.log_event(session["session"]["session_id"], "A02", "scroll", {"scroll_y": 100}, 1200, "e3")
    reading = service.finish_reading(session["session"]["session_id"], 1, "A02", 5000, 1000)
    assert reading["initial_reading_time_ms"] == 4000
    assert reading["normalized_scroll_distance"] == pytest.approx(0.5)
    events = db.list_events(session["session"]["session_id"])
    assert [e["event_id"] for e in events][1:] == ["e1", "e2", "e3"]
    db.close()


def test_formal_and_pilot_data_are_separated(tmp_path):
    db, service = make_service(tmp_path)
    pilot = service.start_or_resume("P05", "client-a", mode="pilot")
    formal = service.start_or_resume("P06", "client-b", mode="formal")
    db.log_event(pilot["session"]["session_id"], "A02", "test", {"x": 1}, 1, "pilot-event")
    db.log_event(formal["session"]["session_id"], "A02", "test", {"x": 2}, 2, "formal-event")
    assert {e["event_id"] for e in db.list_events(mode="formal")} == {"formal-event"}
    assert {e["event_id"] for e in db.list_events(mode="pilot")} == {"pilot-event"}
    db.close()


def test_workload_values_are_validated_and_cannot_be_overwritten(tmp_path):
    db, service = make_service(tmp_path)
    session = service.start_or_resume("P07", "client-a", mode="pilot")
    with pytest.raises(ValueError):
        service.submit_workload(session["session"]["session_id"], 1, {
            "mental_demand": 0, "physical_demand": 4, "temporal_demand": 4,
            "performance": 4, "effort": 4, "frustration": 4,
            "reading_continuity": 0, "comment_accessibility": 8,
        })
    db.close()


def test_workload_nasa_dimensions_use_a_compact_one_to_seven_scale(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P16", "client-a", mode="pilot")["session"]["session_id"]
    values = {
        "mental_demand": 4, "physical_demand": 1, "temporal_demand": 7,
        "performance": 3, "effort": 5, "frustration": 2,
        "reading_continuity": 6, "comment_accessibility": 7,
    }
    service.submit_workload(sid, 1, values)
    with pytest.raises(ValueError):
        service.submit_workload(sid, 2, {**values, "mental_demand": 8})
    db.close()


def test_interview_requires_exactly_four_known_answers(tmp_path):
    db, service = make_service(tmp_path)
    session = service.start_or_resume("P08", "client-a", mode="pilot")
    with pytest.raises(ValueError):
        service.submit_interview(session["session"]["session_id"], {"q1": "ok"}, 1000)
    db.close()


def test_submitted_workload_cannot_be_changed(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P10", "client-a", mode="pilot")["session"]["session_id"]
    values = {
        "mental_demand": 4, "physical_demand": 2, "temporal_demand": 3,
        "performance": 5, "effort": 4, "frustration": 2,
        "reading_continuity": 6, "comment_accessibility": 7,
    }
    service.submit_workload(sid, 1, values)
    with pytest.raises(DuplicateSubmissionError):
        service.submit_workload(sid, 1, values)
    db.close()


def test_preference_requires_unique_complete_ranking(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P11", "client-a", mode="pilot")["session"]["session_id"]
    with pytest.raises(ValueError):
        service.submit_preference(sid, ["TE", "TE", "SE", "BL"], "TE", "reason")
    db.close()


def test_complete_four_article_workflow_persists_all_required_records(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P13", "client-a", mode="pilot")["session"]["session_id"]
    values = {
        "mental_demand": 4, "physical_demand": 2, "temporal_demand": 3,
        "performance": 5, "effort": 4, "frustration": 2,
        "reading_continuity": 6, "comment_accessibility": 7,
    }
    for order in range(1, 5):
        article = service.db.get_articles(sid)[order - 1]
        service.advance_stage(sid, "reading", order)
        service.record_reading_start(sid, order, article["article_id"], order * 1000)
        service.finish_reading(sid, order, article["article_id"], order * 1000 + 100, 1000)
        for group in ("cra", "aca", "ctia", "location"):
            for question in service.materials[article["article_id"]]["questions"][group]:
                service.submit_response(sid, order, article["article_id"], group, question["id"], question["answer"], 2000, 2100)
            service.advance_stage(sid, "workload" if group == "location" else {"cra": "aca", "aca": "ctia", "ctia": "location"}[group], order)
        service.submit_workload(sid, order, values)
    service.submit_preference(sid, ["TE", "CS", "SE", "BL"], "TE", "reason")
    completed = service.submit_interview(sid, {"q1": "a", "q2": "b", "q3": "c", "q4": "d"}, 9000)
    assert completed["status"] == "completed"
    assert len(db.list_responses(sid)) == 40
    assert db._one("SELECT COUNT(*) AS n FROM workload_surveys WHERE session_id = ?", (sid,))["n"] == 4
    db.close()


def test_interaction_metrics_are_persisted_at_article_question_and_event_levels(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P15", "client-a", mode="pilot")["session"]["session_id"]
    article_id = db.get_articles(sid)[0]["article_id"]

    service.log_event(
        sid, article_id, "scroll",
        {"article_order": 1, "stage": "reading", "scroll_y": 420, "viewport_height": 800, "document_height": 4000},
        1000, "scroll-1",
    )
    event = db.list_events(sid)[0]
    assert event["article_order"] == 1
    assert event["stage"] == "reading"

    service.record_reading_start(sid, 1, article_id, 1000)
    reading = service.finish_reading(
        sid, 1, article_id, 5000, 4000,
        normalized_scroll_distance=0.75,
        comment_interaction_count=7,
        start_ms=1000,
        scroll_event_count=12,
        total_scroll_distance_px=3000,
        max_scroll_y=2400,
        comment_counts={
            "comment_click_count": 3,
            "comment_open_count": 2,
            "comment_close_count": 1,
            "paragraph_toggle_count": 1,
        },
    )
    assert reading["scroll_event_count"] == 12
    assert reading["total_scroll_distance_px"] == 3000
    assert reading["max_scroll_y"] == 2400
    assert reading["comment_click_count"] == 3
    assert reading["comment_open_count"] == 2
    assert reading["comment_close_count"] == 1
    assert reading["paragraph_toggle_count"] == 1

    response = service.submit_response(
        sid, 1, article_id, "cra", "R1", "A", 6000, 7000,
        option_click_count=3, option_change_count=2,
        scroll_event_count=4, total_scroll_distance_px=800, max_scroll_y=500,
    )
    assert response["option_click_count"] == 3
    assert response["option_change_count"] == 2
    assert response["scroll_event_count"] == 4
    assert response["total_scroll_distance_px"] == 800
    assert response["max_scroll_y"] == 500
    db.close()


def test_reading_metrics_fall_back_to_recorded_events_when_client_omits_aggregates(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P16", "client-a", mode="formal")["session"]["session_id"]
    article_id = db.get_articles(sid)[0]["article_id"]
    service.record_reading_start(sid, 1, article_id, 1000)
    for event_id, y, timestamp in (("r1", 0, 1000), ("r2", 250, 1100), ("r3", 125, 1200)):
        service.log_event(sid, article_id, "scroll", {
            "article_order": 1, "stage": "reading", "scroll_y": y,
        }, timestamp, event_id)
    reading = service.finish_reading(
        sid, 1, article_id, 5000, 1000,
        normalized_scroll_distance=None,
        start_ms=1000,
        scroll_event_count=None,
        total_scroll_distance_px=None,
        max_scroll_y=None,
    )
    assert reading["scroll_event_count"] == 3
    assert reading["total_scroll_distance_px"] == pytest.approx(375)
    assert reading["max_scroll_y"] == pytest.approx(250)
    assert reading["normalized_scroll_distance"] == pytest.approx(0.375)
    db.close()


def test_response_metrics_default_safely_when_client_omits_aggregate_values(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P17", "client-a", mode="formal")["session"]["session_id"]
    article_id = db.get_articles(sid)[0]["article_id"]
    response = service.submit_response(
        sid, 1, article_id, "cra", "R1", "A", 1000, 1200,
        option_click_count=None, option_change_count=None,
        scroll_event_count=None, total_scroll_distance_px=None, max_scroll_y=None,
    )
    assert response["option_click_count"] == 1
    assert response["option_change_count"] == 0
    assert response["scroll_event_count"] == 0
    assert response["total_scroll_distance_px"] == 0
    assert response["max_scroll_y"] == 0
    db.close()


def test_export_includes_interaction_metrics_for_analysis(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P18", "client-a", mode="formal")["session"]["session_id"]
    article_id = db.get_articles(sid)[0]["article_id"]
    service.record_reading_start(sid, 1, article_id, 1000)
    service.finish_reading(
        sid, 1, article_id, 5000, 2000,
        normalized_scroll_distance=0.25,
        comment_interaction_count=4,
        start_ms=1000,
        scroll_event_count=2,
        total_scroll_distance_px=500,
        max_scroll_y=400,
        comment_counts={
            "comment_click_count": 2,
            "comment_open_count": 1,
            "comment_close_count": 1,
            "paragraph_toggle_count": 0,
        },
    )
    service.submit_response(
        sid, 1, article_id, "cra", "R1", "A", 6000, 6500,
        option_click_count=2, option_change_count=1,
        scroll_event_count=0, total_scroll_distance_px=0, max_scroll_y=0,
    )
    rows = db.export_rows()
    row = next(item for item in rows if item["session_id"] == sid and item["article_order"] == 1 and item["question_id"] == "R1")
    assert row["article_scroll_event_count"] == 2
    assert row["article_total_scroll_distance_px"] == 500
    assert row["article_max_scroll_y"] == 400
    assert row["comment_click_count"] == 2
    assert row["option_click_count"] == 2
    assert row["option_change_count"] == 1
    db.close()


def test_analysis_export_includes_reading_timestamps_and_raw_event_export(tmp_path):
    db, service = make_service(tmp_path)
    sid = service.start_or_resume("P19", "client-a", mode="formal")["session"]["session_id"]
    article_id = db.get_articles(sid)[0]["article_id"]
    service.record_reading_start(sid, 1, article_id, 1000)
    service.log_event(
        sid, article_id, "comment_click",
        {"article_order": 1, "stage": "reading", "comment_id": "C01"},
        1200, "event-export-1",
    )
    service.finish_reading(sid, 1, article_id, 5000, 2000, start_ms=1000)

    analysis_row = next(row for row in db.export_rows() if row["session_id"] == sid and row["article_order"] == 1)
    assert analysis_row["reading_start_time"] == "1000"
    assert analysis_row["reading_end_time"] == "5000"

    events = db.export_event_rows()
    event = next(row for row in events if row["event_id"] == "event-export-1")
    assert event["event_row_id"] >= 1
    assert event["participant_id"] == "P19"
    assert event["article_order"] == 1
    assert event["stage"] == "reading"
    assert event["question_id"] is None
    assert event["event_type"] == "comment_click"
    assert json.loads(event["payload_json"])["comment_id"] == "C01"
    assert event["client_occurred_at"] == "1200"
    assert event["received_at"]

    csv_text = db.export_events_csv()
    assert "event_id" in csv_text.splitlines()[0]
    assert "event-export-1" in csv_text
    db.close()
