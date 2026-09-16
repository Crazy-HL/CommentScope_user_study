import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from admin_stats import AdminStats  # noqa: E402
from database import ExperimentDatabase  # noqa: E402


def _insert_session(db, sid, pid, article_id, condition, status="completed", article_status="completed"):
    db.conn.execute(
        "INSERT INTO sessions(session_id, participant_id, mode, client_instance_id, status, current_stage, current_article_order, started_at, last_seen_at, completed_at) VALUES (?, ?, 'formal', ?, ?, 'complete', 1, ?, ?, ?)",
        (sid, pid, f"client-{pid}", status, "2026-09-13T00:00:00+00:00", "2026-09-13T00:01:00+00:00", "2026-09-13T00:02:00+00:00" if status == "completed" else None),
    )
    db.conn.execute(
        "INSERT INTO article_sessions(session_id, article_order, article_id, condition, status, current_stage, reading_start_time, reading_end_time, initial_reading_time_ms, document_height, normalized_scroll_distance, comment_interaction_count, scroll_event_count, total_scroll_distance_px, max_scroll_y, comment_click_count, comment_open_count, comment_close_count, paragraph_toggle_count, started_at, completed_at) VALUES (?, 1, ?, ?, ?, 'reading', ?, ?, ?, 1000, ?, 3, 2, 200, 200, 1, 1, 0, 0, ?, ?)",
        (sid, article_id, condition, article_status, "1000", "11000", 10000 if sid.endswith("1") else 20000, 0.1 if sid.endswith("1") else 0.2, "2026-09-13T00:00:00+00:00", "2026-09-13T00:02:00+00:00" if article_status == "completed" else None),
    )
    db.conn.commit()


def _insert_responses(db, sid, values):
    for question_type, count, correct_values, elapsed_values in values:
        for index in range(count):
            db.conn.execute(
                "INSERT INTO responses(session_id, article_order, article_id, question_type, question_id, selected_option, correct, item_start_time, submit_time, elapsed_ms) VALUES (?, 1, 'A02', ?, ?, 'A', ?, ?, ?, ?)",
                (sid, question_type, f"{question_type}-{index + 1}", int(correct_values[index]), "1000", "2000", int(elapsed_values[index])),
            )
    db.conn.commit()


@pytest.fixture
def db_with_fixture(tmp_path):
    db = ExperimentDatabase(tmp_path / "stats.sqlite3")
    _insert_session(db, "session-1", "P01", "A02", "TE")
    _insert_session(db, "session-2", "P02", "A02", "TE")
    _insert_session(db, "session-3", "P03", "A03", "CS")
    _insert_session(db, "session-4", "P04", "A03", "CS")
    for sid in ("session-1", "session-2", "session-3", "session-4"):
        _insert_responses(db, sid, [
            ("cra", 4, [1, 1, 1, 0], [400, 500, 600, 700]),
            ("aca", 2, [1, 0], [800, 900]),
            ("cti", 2, [1, 0] if sid in {"session-1", "session-3"} else [1, 1], [1000, 2000]),
            ("location", 2, [1, 1], [3000, 4000]),
        ])
        db.conn.execute(
            "INSERT INTO workload_surveys(session_id, article_order, mental_demand, physical_demand, temporal_demand, performance, effort, frustration, reading_continuity, comment_accessibility, submitted_at) VALUES (?, 1, 4, 2, 3, 5, 4, 2, 6, 5, ?)",
            (sid, "2026-09-13T00:03:00+00:00"),
        )
    db.conn.execute("INSERT INTO preferences(session_id, ranking_json, preferred_condition, reason, submitted_at) VALUES ('session-1', ?, 'TE', 'reason', ?)", (json.dumps(["TE", "CS", "SE", "BL"]), "2026-09-13T00:04:00+00:00"))
    db.conn.execute("INSERT INTO interviews(session_id, answers_json, started_at, submitted_at) VALUES ('session-1', ?, ?, ?)", (json.dumps({"q1": "a", "q2": "b", "q3": "c", "q4": "d"}), "2026-09-13T00:05:00+00:00", "2026-09-13T00:06:00+00:00"))
    db.conn.commit()
    yield db
    db.close()


def test_ctia_and_ctirt_are_aggregated_per_article_session(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    assert result["metrics"]["CTIA"]["TE"]["n"] == 2
    assert result["metrics"]["CTIA"]["TE"]["mean"] == 0.75
    assert result["metrics"]["CTIRT"]["TE"]["mean"] == 1500.0


def test_all_article_and_subjective_metrics_are_available(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})["metrics"]
    assert result["CRA"]["TE"]["mean"] == 0.75
    assert result["ACA"]["TE"]["mean"] == 0.5
    assert result["CLA"]["TE"]["mean"] == 1.0
    assert result["CLT"]["TE"]["mean"] == 3500.0
    assert result["Initial Reading Time"]["TE"]["mean"] == 15000.0
    assert result["NSD"]["TE"]["mean"] == 0.15000000000000002
    assert result["RC"]["TE"]["mean"] == 6.0
    assert result["CA"]["TE"]["mean"] == 5.0
    assert result["NASA-TLX Mental Demand"]["TE"]["mean"] == 4.0
    assert result["NASA-TLX Effort"]["TE"]["mean"] == 4.0
    assert result["NASA-TLX Frustration"]["TE"]["mean"] == 2.0


def test_filters_limit_article_sessions_and_empty_metrics_are_safe(db_with_fixture):
    stats = AdminStats(db_with_fixture)
    filtered = stats.summary({"condition": "CS", "article_id": "A03"})
    assert filtered["metrics"]["CTIA"]["TE"]["n"] == 0
    assert filtered["metrics"]["CTIA"]["CS"]["n"] == 2
    assert filtered["overview"]["article_sessions_started"] == 2

    empty = stats.summary({"participant_id": "P99"})
    assert empty["metrics"]["CTIA"]["TE"]["n"] == 0
    assert empty["metrics"]["CTIA"]["TE"]["mean"] is None
    assert empty["metrics"]["CTIA"]["TE"]["observations"] == []


def test_summary_contains_expected_progress_counts_and_preferences(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    assert result["overview"]["expected_participants"] == 24
    assert result["overview"]["participants_started"] == 4
    assert result["overview"]["article_sessions_completed"] == 4
    assert result["overview"]["responses"]["total"] == 40
    assert result["overview"]["responses"]["cra"] == 16
    assert result["overview"]["responses"]["cti"] == 8
    assert result["overview"]["surveys"] == 4
    assert result["overview"]["preferences"] == 1
    assert result["overview"]["interviews"] == 1
    assert result["preference"]["preferred_condition"]["TE"] == 1


def test_active_article_session_is_excluded_by_completed_filter(db_with_fixture):
    _insert_session(db_with_fixture, "session-active", "P05", "A04", "SE", status="active", article_status="active")
    result = AdminStats(db_with_fixture).summary({"status": "completed"})
    assert result["metrics"]["CTIA"]["SE"]["n"] == 0
    assert result["overview"]["article_sessions_started"] == 4


def test_analysis_is_descriptive_and_names_highest_ctia_condition(db_with_fixture):
    result = AdminStats(db_with_fixture).analysis({})
    statement = next(item for item in result["statements"] if item["metric"] == "CTIA")
    assert "CTIA" in statement["text"]
    assert statement["evidence"]["highest_condition"] == "TE"
    assert "显著差异" not in statement["text"]


def test_data_quality_reports_missing_completed_task_data_and_expected_count_gap(db_with_fixture):
    db_with_fixture.conn.execute("DELETE FROM responses WHERE session_id = 'session-1' AND question_type = 'cra' AND question_id = 'cra-4'")
    db_with_fixture.conn.execute("DELETE FROM workload_surveys WHERE session_id = 'session-1'")
    db_with_fixture.conn.commit()
    result = AdminStats(db_with_fixture).data_quality({})
    codes = {issue["code"] for issue in result["issues"]}
    assert "missing_cra" in codes
    assert "missing_workload" in codes
    assert result["observed"]["article_sessions"] == 4
    assert result["observed"]["responses"]["cra"] == 15
    assert "incomplete_expected_counts" in codes


def test_summary_uses_participant_targets_for_preference_and_interview_progress(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    overview = result["overview"]
    assert overview["preference_submitted"] == 1
    assert overview["preference_reason_submitted"] == 1
    assert overview["interviews"] == 1
    assert overview["preferences_expected"] == 24
    assert overview["preference_reasons_expected"] == 24
    assert overview["interviews_expected"] == 24


def test_summary_supports_article_order_filter(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({"article_order": "1"})
    assert result["scope"]["article_order"] == "1"
    assert result["overview"]["article_sessions_completed"] == 4


def test_summary_returns_complete_participant_details_for_selected_participant(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({"participant_id": "P01"})

    assert len(result["participant_details"]) == 1
    detail = result["participant_details"][0]
    assert detail["participant_id"] == "P01"
    assert detail["article_id"] == "A02"
    assert detail["article_order"] == 1
    assert detail["condition"] == "TE"
    assert detail["initial_reading_time_ms"] == 10000
    assert detail["responses"]["cra"][0]["question_id"] == "cra-1"
    assert detail["workload"]["reading_continuity"] == 6
    assert result["participant_tasks"][0]["preference"]["preferred_condition"] == "TE"
    assert result["participant_tasks"][0]["interview"]["answers"]["q1"] == "a"


def test_participant_details_ignore_article_filters_when_participant_is_selected(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({"participant_id": "P01", "article_id": "A03"})
    assert [detail["article_id"] for detail in result["participant_details"]] == ["A02"]


def test_filter_options_keep_all_predefined_participants_selectable(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    assert result["filter_options"]["participants"] == [f"P{index:02d}" for index in range(1, 25)]


def test_selected_participant_details_include_all_article_data_despite_summary_filters(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({
        "participant_id": "P01",
        "article_id": "A03",
        "condition": "CS",
        "article_order": "2",
    })

    # The aggregate tables respect the active filters, but the explicit participant
    # detail view must remain a complete participant record.
    assert result["participant_details"]
    assert [detail["article_id"] for detail in result["participant_details"]] == ["A02"]
    assert len(result["participant_tasks"]) == 1


def test_article_sequence_filter_accepts_complete_display_sequences():
    stats = AdminStats(None)
    assert stats.normalize_filters({"article_sequence": "01-02-03-04"})["article_sequence"] == "01-02-03-04"
    assert stats.normalize_filters({"article_sequence": "04-01-02-03"})["article_sequence"] == "04-01-02-03"


@pytest.mark.parametrize("sequence", ["01-02-03", "A02-A03-A04-A07", "01-01-02-03", "05-01-02-03"])
def test_article_sequence_filter_rejects_invalid_sequences(sequence):
    with pytest.raises(ValueError, match="invalid article_sequence"):
        AdminStats.normalize_filters({"article_sequence": sequence})


def test_article_sequence_filter_selects_the_matching_allocation_group(db_with_fixture):
    _insert_session(db_with_fixture, "session-7", "P07", "A03", "SE")
    result = AdminStats(db_with_fixture).summary({"article_sequence": "02-03-04-01"})
    assert result["scope"]["article_sequence"] == "02-03-04-01"
    assert result["overview"]["article_sessions_started"] == 1
    assert result["filter_options"]["article_sequences"] == [
        "01-02-03-04", "02-03-04-01", "03-04-01-02", "04-01-02-03"
    ]


def test_article_sequence_filter_scopes_all_participants_in_the_matching_group(db_with_fixture):
    for index in range(7, 13):
        _insert_session(db_with_fixture, f"sequence-session-{index}", f"P{index:02d}", "A03", "SE")

    result = AdminStats(db_with_fixture).summary({"article_sequence": "02-03-04-01"})

    assert result["overview"]["participants_started"] == 6
    assert result["overview"]["article_sessions_started"] == 6
    assert {row["participant_id"] for row in result["participant_details"]} == set()
    assert result["scope"]["article_sequence"] == "02-03-04-01"


def test_article_sequence_and_article_position_filters_can_be_combined(db_with_fixture):
    _insert_session(db_with_fixture, "session-7", "P07", "A03", "SE")
    result = AdminStats(db_with_fixture).summary({
        "article_sequence": "02-03-04-01",
        "article_order": "1",
        "article_id": "A03",
    })
    assert result["overview"]["article_sessions_started"] == 1
    assert result["scope"]["article_order"] == "1"


def test_article_sequence_scope_takes_precedence_over_participant_filter(db_with_fixture):
    _insert_session(db_with_fixture, "sequence-session-7", "P07", "A03", "SE")
    result = AdminStats(db_with_fixture).summary({
        "participant_id": "P01",
        "article_sequence": "02-03-04-01",
    })

    assert result["overview"]["participants_started"] == 1
    assert result["overview"]["article_sessions_started"] == 1
    assert result["scope"]["participant_id"] == ""
    assert result["scope"]["article_sequence"] == "02-03-04-01"


def test_summary_includes_all_predefined_participants_in_overview_table(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({})
    rows = result["participant_overview"]

    assert len(rows) == 24
    assert rows[0]["participant_id"] == "P01"
    assert rows[-1]["participant_id"] == "P24"
    assert rows[0]["group_id"] == "G1"
    assert rows[0]["article_sequence"] == "01-02-03-04"
    assert rows[0]["article_sessions_completed"] == 1
    assert rows[0]["responses_count"] == 10
    assert rows[0]["surveys_count"] == 1
    assert rows[0]["preference_submitted"] is True
    assert rows[0]["interview_submitted"] is True
    assert rows[-1]["session_status"] == "not_started"
    assert rows[-1]["article_sessions_completed"] == 0
    assert rows[-1]["responses_count"] == 0


def test_article_sequence_overview_includes_all_six_participants(db_with_fixture):
    result = AdminStats(db_with_fixture).summary({"article_sequence": "02-03-04-01"})
    rows = result["participant_overview"]

    assert [row["participant_id"] for row in rows] == ["P07", "P08", "P09", "P10", "P11", "P12"]
    assert all(row["article_sequence"] == "02-03-04-01" for row in rows)
