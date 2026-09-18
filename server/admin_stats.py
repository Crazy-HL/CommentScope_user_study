"""Server-side descriptive statistics for the researcher dashboard."""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from experiment_config import GROUP_ALLOCATIONS, PARTICIPANTS


CONDITIONS = ("TE", "CS", "SE", "BL")
ARTICLES = ("A02", "A03", "A04", "A07")
ARTICLE_DISPLAY_SEQUENCES = ("01-02-03-04", "02-03-04-01", "03-04-01-02", "04-01-02-03")
SEQUENCE_TO_GROUP = dict(zip(ARTICLE_DISPLAY_SEQUENCES, ("G1", "G2", "G3", "G4")))
VALID_STATUSES = ("active", "completed")
EXPECTED = {
    "participants": 24,
    "article_sessions": 96,
    "responses": 960,
    "responses_by_type": {"cra": 384, "aca": 192, "cti": 192, "location": 192},
    "surveys": 96,
    "preferences": 24,
    "interviews": 24,
}

METRIC_NAMES = (
    "CTIA", "CTIRT", "CRA", "ACA", "CLA", "CLT",
    "Initial Reading Time", "NSD", "Scroll Events", "Total Scroll Distance", "Max Scroll Y",
    "Comment Interaction Count", "Comment Click Count", "Comment Open Count", "Comment Close Count",
    "Paragraph Toggle Count", "RC", "CA",
    "NASA-TLX Mental Demand", "NASA-TLX Physical Demand", "NASA-TLX Temporal Demand",
    "NASA-TLX Performance", "NASA-TLX Effort", "NASA-TLX Frustration",
)


def metric_summary(values: Iterable[float]) -> dict:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "stddev": None,
            "ci95": None,
            "observations": [],
        }
    mean = sum(cleaned) / len(cleaned)
    stddev = statistics.stdev(cleaned) if len(cleaned) > 1 else 0.0
    ci95 = 1.96 * stddev / math.sqrt(len(cleaned)) if len(cleaned) > 1 else 0.0
    return {
        "n": len(cleaned),
        "mean": mean,
        "median": statistics.median(cleaned),
        "stddev": stddev,
        "ci95": ci95,
        "observations": cleaned,
    }


def _empty_metric_map() -> dict:
    return {name: {condition: metric_summary([]) for condition in CONDITIONS} for name in METRIC_NAMES}


def _normalize_question_type(value: str) -> str:
    value = str(value or "").strip().lower()
    aliases = {
        "cra": "cra",
        "recognition": "cra",
        "aca": "aca",
        "article_comprehension": "aca",
        "cti": "cti",
        "ctia": "cti",
        "ctirt": "cti",
        "location": "location",
        "cla": "location",
        "clt": "location",
    }
    return aliases.get(value, value)


class AdminStats:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def normalize_filters(filters: Optional[Mapping[str, str]]) -> dict:
        filters = filters or {}
        normalized = {
            key: str(filters.get(key, "")).strip()
            for key in ("participant_id", "article_id", "condition", "status", "article_order", "article_sequence")
        }
        if normalized["article_id"] and normalized["article_id"] not in ARTICLES:
            raise ValueError("invalid article_id")
        if normalized["condition"] and normalized["condition"] not in CONDITIONS:
            raise ValueError("invalid condition")
        if normalized["status"] and normalized["status"] not in VALID_STATUSES:
            raise ValueError("invalid status")
        if normalized["article_order"]:
            try:
                article_order = int(normalized["article_order"])
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid article_order") from exc
            if article_order not in (1, 2, 3, 4):
                raise ValueError("invalid article_order")
            normalized["article_order"] = str(article_order)
        if normalized["article_sequence"] and normalized["article_sequence"] not in SEQUENCE_TO_GROUP:
            raise ValueError("invalid article_sequence")
        # A complete article sequence is a participant-group scope. If stale
        # UI state also sends participant_id, the group-wide sequence must win
        # instead of producing an accidental empty intersection.
        if normalized["article_sequence"]:
            normalized["participant_id"] = ""
        return normalized

    def _article_rows(self, filters: Optional[Mapping[str, str]] = None) -> List[dict]:
        filters = self.normalize_filters(filters)
        clauses = ["s.status != 'reset'"]
        params: List[str] = []
        fixed = {
            "participant_id": "s.participant_id",
            "article_id": "a.article_id",
            "condition": "a.condition",
            "status": "a.status",
            "article_order": "a.article_order",
        }
        for key, column in fixed.items():
            if filters[key]:
                clauses.append(f"{column} = ?")
                params.append(filters[key])
        if filters["article_sequence"]:
            group_id = SEQUENCE_TO_GROUP[filters["article_sequence"]]
            participant_ids = [participant_id for participant_id, participant_group in PARTICIPANTS.items() if participant_group == group_id]
            if not participant_ids:
                return []
            placeholders = ",".join("?" for _ in participant_ids)
            clauses.append(f"s.participant_id IN ({placeholders})")
            params.extend(participant_ids)
        query = """
            SELECT a.*, s.participant_id, s.mode, s.status AS session_status,
                   s.started_at AS session_started_at, s.completed_at AS session_completed_at
            FROM article_sessions a
            JOIN sessions s ON s.session_id = a.session_id
            WHERE """ + " AND ".join(clauses) + " ORDER BY s.participant_id, a.article_order"
        return self.db._many(query, params)

    def _responses_for_rows(self, rows: Sequence[dict]) -> Dict[Tuple[str, int], List[dict]]:
        if not rows:
            return {}
        keys = {(row["session_id"], int(row["article_order"])) for row in rows}
        sessions = sorted({key[0] for key in keys})
        placeholders = ",".join("?" for _ in sessions)
        all_responses = self.db._many(
            f"SELECT * FROM responses WHERE session_id IN ({placeholders}) ORDER BY response_id",
            sessions,
        )
        grouped: Dict[Tuple[str, int], List[dict]] = defaultdict(list)
        for response in all_responses:
            key = (response["session_id"], int(response["article_order"]))
            if key in keys:
                grouped[key].append(response)
        return grouped

    def _workloads_for_rows(self, rows: Sequence[dict]) -> Dict[Tuple[str, int], dict]:
        if not rows:
            return {}
        keys = {(row["session_id"], int(row["article_order"])) for row in rows}
        sessions = sorted({key[0] for key in keys})
        placeholders = ",".join("?" for _ in sessions)
        surveys = self.db._many(
            f"SELECT * FROM workload_surveys WHERE session_id IN ({placeholders}) ORDER BY submitted_at",
            sessions,
        )
        return {
            (survey["session_id"], int(survey["article_order"])): survey
            for survey in surveys
            if (survey["session_id"], int(survey["article_order"])) in keys
        }

    def _scope_session_ids(self, rows: Sequence[dict]) -> List[str]:
        return sorted({row["session_id"] for row in rows})

    def _events_for_rows(self, rows: Sequence[dict]) -> Dict[Tuple[str, int], List[dict]]:
        if not rows:
            return {}
        keys = {(row["session_id"], int(row["article_order"])) for row in rows}
        sessions = sorted({key[0] for key in keys})
        placeholders = ",".join("?" for _ in sessions)
        events = self.db._many(
            f"SELECT * FROM events WHERE session_id IN ({placeholders}) ORDER BY event_row_id",
            sessions,
        )
        grouped: Dict[Tuple[str, int], List[dict]] = defaultdict(list)
        for event in events:
            event_order = event.get("article_order")
            matching_keys = [
                key for key in keys
                if key[0] == event.get("session_id")
                and (event_order is not None and int(event_order) == key[1] or event_order is None and event.get("article_id") == next((row.get("article_id") for row in rows if row.get("session_id") == key[0] and int(row.get("article_order")) == key[1]), None))
            ]
            for key in matching_keys:
                try:
                    payload = json.loads(event.get("payload_json") or "{}")
                except (TypeError, json.JSONDecodeError):
                    payload = event.get("payload_json")
                detail = dict(event)
                detail["payload"] = payload
                grouped[key].append(detail)
        return grouped

    @staticmethod
    def _detail_response_groups(items: Sequence[dict]) -> dict:
        grouped: Dict[str, List[dict]] = defaultdict(list)
        for item in items:
            response = dict(item)
            response["task_type"] = _normalize_question_type(response.get("question_type"))
            grouped[response["task_type"]].append(response)
        return dict(grouped)

    @staticmethod
    def _article_detail(row: dict, items: Sequence[dict], workload: Optional[dict], events: Sequence[dict]) -> dict:
        by_type: Dict[str, List[dict]] = defaultdict(list)
        for response in items:
            by_type[_normalize_question_type(response.get("question_type"))].append(response)
        scores = {}
        for metric, question_type, required in (("CRA", "cra", 4), ("ACA", "aca", 2), ("CTIA", "cti", 2), ("CLA", "location", 2)):
            values = by_type.get(question_type, [])[:required]
            scores[metric] = sum(int(item.get("correct", 0)) for item in values) / required if len(values) >= required else None
        for metric, question_type, required in (("CTIRT", "cti", 2), ("CLT", "location", 2)):
            values = by_type.get(question_type, [])[:required]
            scores[metric] = sum(float(item.get("elapsed_ms", 0)) for item in values) / required if len(values) >= required else None
        detail = dict(row)
        detail.update(scores)
        detail["responses"] = AdminStats._detail_response_groups(items)
        detail["responses_total"] = len(items)
        detail["workload"] = dict(workload) if workload else None
        detail["events"] = [dict(event) for event in events]
        return detail

    def _participant_tasks(self, session_ids: Sequence[str]) -> List[dict]:
        if not session_ids:
            return []
        placeholders = ",".join("?" for _ in session_ids)
        sessions = self.db._many(
            f"SELECT session_id, participant_id, mode, status, started_at, last_seen_at, completed_at FROM sessions WHERE session_id IN ({placeholders}) ORDER BY participant_id",
            list(session_ids),
        )
        preferences = {row["session_id"]: row for row in self.db._many(f"SELECT * FROM preferences WHERE session_id IN ({placeholders})", list(session_ids))}
        interviews = {row["session_id"]: row for row in self.db._many(f"SELECT * FROM interviews WHERE session_id IN ({placeholders})", list(session_ids))}
        result = []
        for session in sessions:
            preference = preferences.get(session["session_id"])
            interview = interviews.get(session["session_id"])
            preference_detail = None
            interview_detail = None
            if preference:
                try:
                    ranking = json.loads(preference.get("ranking_json") or "[]")
                except (TypeError, json.JSONDecodeError):
                    ranking = []
                preference_detail = dict(preference)
                preference_detail["ranking"] = ranking
            if interview:
                try:
                    answers = json.loads(interview.get("answers_json") or "{}")
                except (TypeError, json.JSONDecodeError):
                    answers = {}
                interview_detail = dict(interview)
                interview_detail["answers"] = answers
            result.append({
                **session,
                "preference": preference_detail,
                "interview": interview_detail,
            })
        return result

    def _participant_details(self, rows: Sequence[dict], responses: Mapping[Tuple[str, int], Sequence[dict]], workloads: Mapping[Tuple[str, int], dict]) -> List[dict]:
        if not rows:
            return []
        events = self._events_for_rows(rows)
        return [
            self._article_detail(
                row,
                responses.get((row["session_id"], int(row["article_order"])), []),
                workloads.get((row["session_id"], int(row["article_order"]))),
                events.get((row["session_id"], int(row["article_order"])), []),
            )
            for row in rows
        ]

    def _responses_counts(self, responses: Mapping[Tuple[str, int], Sequence[dict]]) -> dict:
        counts = Counter()
        for items in responses.values():
            for response in items:
                counts[_normalize_question_type(response.get("question_type"))] += 1
        return {
            "total": sum(counts.values()),
            "cra": counts["cra"],
            "aca": counts["aca"],
            "cti": counts["cti"],
            "location": counts["location"],
        }

    def _preference_stats(self, session_ids: Sequence[str]) -> dict:
        if not session_ids:
            return {"rank": {condition: metric_summary([]) for condition in CONDITIONS}, "rank_one": {condition: 0 for condition in CONDITIONS}, "rank_four": {condition: 0 for condition in CONDITIONS}, "preferred_condition": {condition: 0 for condition in CONDITIONS}, "submitted": 0, "reason_submitted": 0}
        placeholders = ",".join("?" for _ in session_ids)
        rows = self.db._many(f"SELECT * FROM preferences WHERE session_id IN ({placeholders})", list(session_ids))
        ranks = {condition: [] for condition in CONDITIONS}
        rank_one = {condition: 0 for condition in CONDITIONS}
        rank_four = {condition: 0 for condition in CONDITIONS}
        preferred = Counter()
        reason_submitted = 0
        for row in rows:
            try:
                ranking = json.loads(row["ranking_json"])
            except (TypeError, json.JSONDecodeError):
                ranking = []
            if isinstance(ranking, dict):
                ranking = [condition for condition, _ in sorted(ranking.items(), key=lambda item: item[1])]
            if not isinstance(ranking, list):
                ranking = []
            for index, condition in enumerate(ranking, start=1):
                if condition in CONDITIONS:
                    ranks[condition].append(index)
                    if index == 1:
                        rank_one[condition] += 1
                    if index == 4:
                        rank_four[condition] += 1
            if row.get("preferred_condition") in CONDITIONS:
                preferred[row["preferred_condition"]] += 1
            if str(row.get("reason") or "").strip():
                reason_submitted += 1
        return {
            "rank": {condition: metric_summary(ranks[condition]) for condition in CONDITIONS},
            "rank_one": {condition: rank_one[condition] for condition in CONDITIONS},
            "rank_four": {condition: rank_four[condition] for condition in CONDITIONS},
            "preferred_condition": {condition: preferred[condition] for condition in CONDITIONS},
            "submitted": len(rows),
            "reason_submitted": reason_submitted,
        }

    def _participant_overview(
        self,
        filters: Mapping[str, str],
        rows: Sequence[dict],
        responses: Mapping[Tuple[str, int], Sequence[dict]],
        workloads: Mapping[Tuple[str, int], dict],
    ) -> List[dict]:
        """Return one progress/data row for every participant in the current scope.

        Unlike ``participant_details``, this is intentionally participant-level and
        keeps pre-assigned participants with no database rows visible as
        ``not_started``. Article/session filters affect the counts in each row,
        while the participant or complete-sequence filter determines who is in the
        table.
        """
        filters = self.normalize_filters(filters)
        observed_participants = {row.get("participant_id") for row in rows if row.get("participant_id")}
        if filters["participant_id"]:
            participant_ids = [filters["participant_id"]]
        elif filters["article_sequence"]:
            group_id = SEQUENCE_TO_GROUP[filters["article_sequence"]]
            participant_ids = [pid for pid, participant_group in PARTICIPANTS.items() if participant_group == group_id]
        else:
            participant_ids = list(PARTICIPANTS)
            participant_ids.extend(sorted(observed_participants - set(participant_ids)))

        # A status filter is a participant-scope filter. Other article/session
        # filters intentionally do not remove participants with zero matches.
        if filters["status"]:
            status_participants = {
                row.get("participant_id") for row in rows
                if row.get("participant_id") and row.get("status") == filters["status"]
            }
            participant_ids = [pid for pid in participant_ids if pid in status_participants]

        if not participant_ids:
            return []

        placeholders = ",".join("?" for _ in participant_ids)
        session_rows = self.db._many(
            f"SELECT session_id, participant_id, status, started_at, last_seen_at, completed_at "
            f"FROM sessions WHERE status != 'reset' AND participant_id IN ({placeholders}) "
            "ORDER BY participant_id, last_seen_at",
            participant_ids,
        )
        sessions_by_participant: Dict[str, List[dict]] = defaultdict(list)
        for session in session_rows:
            sessions_by_participant[session["participant_id"]].append(session)

        rows_by_participant: Dict[str, List[dict]] = defaultdict(list)
        for row in rows:
            participant_id = row.get("participant_id")
            if participant_id in participant_ids:
                rows_by_participant[participant_id].append(row)

        selected_session_ids_by_participant: Dict[str, set] = defaultdict(set)
        for participant_id, participant_rows in rows_by_participant.items():
            selected_session_ids_by_participant[participant_id] = {row["session_id"] for row in participant_rows}

        preferences_by_session: Dict[str, dict] = {}
        interviews_by_session: Dict[str, dict] = {}
        all_session_ids = [session["session_id"] for session in session_rows]
        if all_session_ids:
            session_placeholders = ",".join("?" for _ in all_session_ids)
            preferences_by_session = {
                row["session_id"]: row
                for row in self.db._many(
                    f"SELECT session_id, reason FROM preferences WHERE session_id IN ({session_placeholders})",
                    all_session_ids,
                )
            }
            interviews_by_session = {
                row["session_id"]: row
                for row in self.db._many(
                    f"SELECT session_id FROM interviews WHERE session_id IN ({session_placeholders})",
                    all_session_ids,
                )
            }

        expected_sessions = 1 if any(filters[key] for key in ("article_id", "condition", "article_order")) else 4
        sequence_by_group = {group: sequence for sequence, group in SEQUENCE_TO_GROUP.items()}
        result = []
        for participant_id in participant_ids:
            participant_sessions = sessions_by_participant.get(participant_id, [])
            participant_rows = rows_by_participant.get(participant_id, [])
            selected_session_ids = selected_session_ids_by_participant.get(participant_id, set())
            selected_response_count = sum(
                len(responses.get((row["session_id"], int(row["article_order"])), []))
                for row in participant_rows
            )
            selected_workload_count = sum(
                1 for row in participant_rows
                if (row["session_id"], int(row["article_order"])) in workloads
            )
            selected_preferences = [
                preferences_by_session[session_id]
                for session_id in selected_session_ids
                if session_id in preferences_by_session
            ]
            selected_interviews = sum(
                session_id in interviews_by_session for session_id in selected_session_ids
            )
            if participant_sessions:
                latest_session = participant_sessions[-1]
                session_status = latest_session.get("status") or "active"
                last_seen_at = max((session.get("last_seen_at") for session in participant_sessions if session.get("last_seen_at")), default=None)
            else:
                session_status = "not_started"
                last_seen_at = None

            group_id = PARTICIPANTS.get(participant_id)
            result.append({
                "participant_id": participant_id,
                "group_id": group_id,
                "article_sequence": sequence_by_group.get(group_id),
                "session_status": session_status,
                "article_sessions_expected": expected_sessions,
                "article_sessions_started": sum(row.get("status") in {"active", "completed"} for row in participant_rows),
                "article_sessions_completed": sum(row.get("status") == "completed" for row in participant_rows),
                "responses_count": selected_response_count,
                "surveys_count": selected_workload_count,
                "preference_submitted": bool(selected_preferences),
                "preference_reason_submitted": any(str(row.get("reason") or "").strip() for row in selected_preferences),
                "interview_submitted": bool(selected_interviews),
                "last_seen_at": last_seen_at,
            })
        return result

    def summary(self, filters: Optional[Mapping[str, str]] = None) -> dict:
        filters = self.normalize_filters(filters)
        rows = self._article_rows(filters)
        responses = self._responses_for_rows(rows)
        workloads = self._workloads_for_rows(rows)
        participant_overview = self._participant_overview(filters, rows, responses, workloads)
        metrics = _empty_metric_map()
        complete_rows = [row for row in rows if row.get("status") == "completed"]
        complete_keys = {(row["session_id"], int(row["article_order"])) for row in complete_rows}
        for row in complete_rows:
            key = (row["session_id"], int(row["article_order"]))
            condition = row.get("condition")
            if condition not in CONDITIONS:
                continue
            items = [_response for _response in responses.get(key, [])]
            by_type: Dict[str, List[dict]] = defaultdict(list)
            for response in items:
                by_type[_normalize_question_type(response.get("question_type"))].append(response)
            task_specs = {
                "CRA": ("cra", 4, lambda values: sum(int(item.get("correct", 0)) for item in values) / 4),
                "ACA": ("aca", 2, lambda values: sum(int(item.get("correct", 0)) for item in values) / 2),
                "CTIA": ("cti", 2, lambda values: sum(int(item.get("correct", 0)) for item in values) / 2),
                "CTIRT": ("cti", 2, lambda values: sum(float(item.get("elapsed_ms", 0)) for item in values) / 2),
                "CLA": ("location", 2, lambda values: sum(int(item.get("correct", 0)) for item in values) / 2),
                "CLT": ("location", 2, lambda values: sum(float(item.get("elapsed_ms", 0)) for item in values) / 2),
            }
            for metric, (question_type, required, calculator) in task_specs.items():
                values = by_type.get(question_type, [])
                if len(values) >= required:
                    metrics[metric][condition]["observations"].append(calculator(values[:required]))
            direct_values = {
                "Initial Reading Time": row.get("initial_reading_time_ms"),
                "NSD": row.get("normalized_scroll_distance"),
                "Scroll Events": row.get("scroll_event_count"),
                "Total Scroll Distance": row.get("total_scroll_distance_px"),
                "Max Scroll Y": row.get("max_scroll_y"),
                "Comment Interaction Count": row.get("comment_interaction_count"),
                "Comment Click Count": row.get("comment_click_count"),
                "Comment Open Count": row.get("comment_open_count"),
                "Comment Close Count": row.get("comment_close_count"),
                "Paragraph Toggle Count": row.get("paragraph_toggle_count"),
            }
            for metric, value in direct_values.items():
                if value is not None:
                    metrics[metric][condition]["observations"].append(float(value))
            survey = workloads.get(key)
            if survey:
                for metric, field in {
                    "RC": "reading_continuity", "CA": "comment_accessibility",
                    "NASA-TLX Mental Demand": "mental_demand", "NASA-TLX Physical Demand": "physical_demand",
                    "NASA-TLX Temporal Demand": "temporal_demand", "NASA-TLX Performance": "performance",
                    "NASA-TLX Effort": "effort", "NASA-TLX Frustration": "frustration",
                }.items():
                    if survey.get(field) is not None:
                        metrics[metric][condition]["observations"].append(float(survey[field]))
        for metric in METRIC_NAMES:
            for condition in CONDITIONS:
                observations = metrics[metric][condition]["observations"]
                metrics[metric][condition] = metric_summary(observations)
        session_ids = self._scope_session_ids(rows)
        # The aggregate tables above intentionally follow every active filter.
        # Once an administrator selects a participant, however, the detail view
        # is an explicit request for that participant's complete record.  Rebuild
        # this scope from participant_id alone so a previously selected article,
        # condition, order, or status filter cannot hide the other article blocks
        # or the participant-level preference/interview data.
        participant_details = []
        participant_tasks = []
        if filters.get("participant_id"):
            participant_rows = self._article_rows({"participant_id": filters["participant_id"]})
            participant_responses = self._responses_for_rows(participant_rows)
            participant_workloads = self._workloads_for_rows(participant_rows)
            participant_details = self._participant_details(
                participant_rows, participant_responses, participant_workloads
            )
            participant_tasks = self._participant_tasks(
                self._scope_session_ids(participant_rows)
            )
        placeholders = ",".join("?" for _ in session_ids)
        session_rows = self.db._many(
            f"SELECT session_id, participant_id, status FROM sessions WHERE session_id IN ({placeholders})" if session_ids else "SELECT session_id, participant_id, status FROM sessions WHERE 0",
            session_ids,
        )
        surveys_count = len(workloads)
        preferences_count = 0
        preference_reason_count = 0
        interviews_count = 0
        if session_ids:
            preferences_count = self.db._one(f"SELECT COUNT(*) AS count FROM preferences WHERE session_id IN ({placeholders})", session_ids)["count"]
            preference_reason_count = self.db._one(f"SELECT COUNT(*) AS count FROM preferences WHERE session_id IN ({placeholders}) AND TRIM(COALESCE(reason, '')) != ''", session_ids)["count"]
            interviews_count = self.db._one(f"SELECT COUNT(*) AS count FROM interviews WHERE session_id IN ({placeholders})", session_ids)["count"]
        overview = {
            "expected_participants": EXPECTED["participants"],
            "participants_started": len({row["participant_id"] for row in session_rows}),
            "participants_completed": len({row["participant_id"] for row in session_rows if row["status"] == "completed"}),
            "participants_active": len({row["participant_id"] for row in session_rows if row["status"] == "active"}),
            "participants_with_data": sorted({row["participant_id"] for row in session_rows}),
            "article_sessions_expected": EXPECTED["article_sessions"],
            "article_sessions_started": sum(row.get("status") in {"active", "completed"} for row in rows),
            "article_sessions_completed": sum(row.get("status") == "completed" for row in rows),
            "responses": self._responses_counts(responses),
            "surveys": surveys_count,
            "surveys_expected": EXPECTED["surveys"],
            "preferences": preferences_count,
            "preference_submitted": preferences_count,
            "preference_reason_submitted": preference_reason_count,
            "preferences_expected": EXPECTED["preferences"],
            "preference_reasons_expected": EXPECTED["preferences"],
            "interviews": interviews_count,
            "interviews_expected": EXPECTED["interviews"],
        }
        return {
            "scope": filters,
            "filter_options": {
                "participants": sorted(set(PARTICIPANTS) | {row["participant_id"] for row in session_rows}),
                "articles": list(ARTICLES),
                "conditions": list(CONDITIONS),
                "article_orders": [1, 2, 3, 4],
                "article_sequences": list(ARTICLE_DISPLAY_SEQUENCES),
            },
            "overview": overview,
            "conditions": {
                condition: {
                    "article_sessions": sum(1 for row in complete_rows if row.get("condition") == condition),
                    "participants": len({row["participant_id"] for row in complete_rows if row.get("condition") == condition}),
                }
                for condition in CONDITIONS
            },
            "metrics": metrics,
            "preference": self._preference_stats(session_ids),
            "participant_details": participant_details,
            "participant_tasks": participant_tasks,
            "participant_overview": participant_overview,
            "last_updated_at": self.db._one("SELECT MAX(last_seen_at) AS value FROM sessions") ["value"] if self.db._one("SELECT MAX(last_seen_at) AS value FROM sessions") else None,
        }

    def analysis(self, filters: Optional[Mapping[str, str]] = None) -> dict:
        result = self.summary(filters)
        statements = []
        for metric in ("CTIA", "CTIRT", "CRA", "ACA", "CLA", "CLT", "Initial Reading Time", "NSD", "RC", "CA"):
            available = [(condition, result["metrics"][metric][condition]) for condition in CONDITIONS if result["metrics"][metric][condition]["n"] > 0]
            if len(available) < 2:
                statements.append({"metric": metric, "severity": "info", "text": f"{metric} 当前有效数据不足，暂不进行条件比较。", "evidence": {"available_conditions": [condition for condition, _ in available]}})
                continue
            higher_is_better = metric not in {"CTIRT", "CLT", "Initial Reading Time", "NSD"}
            chosen = max(available, key=lambda item: item[1]["mean"]) if higher_is_better else min(available, key=lambda item: item[1]["mean"])
            other = min(available, key=lambda item: item[1]["mean"]) if higher_is_better else max(available, key=lambda item: item[1]["mean"])
            difference = chosen[1]["mean"] - other[1]["mean"]
            if not higher_is_better:
                difference = other[1]["mean"] - chosen[1]["mean"]
            statements.append({
                "metric": metric,
                "severity": "info",
                "text": f"描述性结果：{metric} 在 {chosen[0]} 条件的{'均值较高' if higher_is_better else '均值较低'}（n={chosen[1]['n']}），与 {other[0]} 的均值差约 {difference:.2f}。该结果不代表统计显著性或因果关系。",
                "evidence": {"highest_condition": chosen[0] if higher_is_better else None, "lowest_condition": chosen[0] if not higher_is_better else None, "comparison_condition": other[0], "difference": difference},
            })
        return {
            "generated_from": {
                "article_sessions": result["overview"]["article_sessions_completed"],
                "responses": result["overview"]["responses"]["total"],
                "surveys": result["overview"]["surveys"],
            },
            "statements": statements,
        }

    def data_quality(self, filters: Optional[Mapping[str, str]] = None) -> dict:
        filters = self.normalize_filters(filters)
        rows = self._article_rows(filters)
        responses = self._responses_for_rows(rows)
        workloads = self._workloads_for_rows(rows)
        issues = []
        completed_rows = [row for row in rows if row.get("status") == "completed"]
        for row in completed_rows:
            key = (row["session_id"], int(row["article_order"]))
            counts = Counter(_normalize_question_type(item.get("question_type")) for item in responses.get(key, []))
            expected = {"cra": 4, "aca": 2, "cti": 2, "location": 2}
            for question_type, expected_count in expected.items():
                if counts[question_type] != expected_count:
                    issues.append({"severity": "warning", "code": f"missing_{question_type}", "message": f"{row['participant_id']} {row['article_id']} 缺少或多出 {question_type.upper()} 题目回答。", "count": 1, "affected": [f"{row['participant_id']}:{row['article_id']}:{row['article_order']}"]})
            if key not in workloads:
                issues.append({"severity": "warning", "code": "missing_workload", "message": f"{row['participant_id']} {row['article_id']} 缺少文章结束后的主观评价。", "count": 1, "affected": [f"{row['participant_id']}:{row['article_id']}:{row['article_order']}"]})
            for field in ("initial_reading_time_ms", "normalized_scroll_distance", "total_scroll_distance_px", "max_scroll_y"):
                value = row.get(field)
                if value is not None and float(value) < 0:
                    issues.append({"severity": "error", "code": "negative_metric", "message": f"{row['participant_id']} {row['article_id']} 的 {field} 为负数。", "count": 1, "affected": [f"{row['participant_id']}:{row['article_id']}:{row['article_order']}"]})
            if row.get("normalized_scroll_distance") is None and int(row.get("scroll_event_count") or 0) > 0:
                issues.append({"severity": "info", "code": "nsd_fallback", "message": f"{row['participant_id']} {row['article_id']} 的 NSD 需要从滚动事件回退计算。", "count": 1, "affected": [f"{row['participant_id']}:{row['article_id']}:{row['article_order']}"]})
        invalid_conditions = self.db._many("SELECT DISTINCT a.condition FROM article_sessions a JOIN sessions s ON s.session_id = a.session_id WHERE s.status != 'reset' AND a.condition NOT IN ('TE', 'CS', 'SE', 'BL')")
        if invalid_conditions:
            issues.append({"severity": "error", "code": "invalid_condition", "message": "存在不在 TE/CS/SE/BL 中的条件值。", "count": len(invalid_conditions), "affected": [row["condition"] for row in invalid_conditions]})
        response_counts = self._responses_counts(responses)
        if not any(filters.values()):
            incomplete = []
            if observed_article_sessions := len(rows) < EXPECTED["article_sessions"]:
                incomplete.append(f"文章区块 {len(rows)}/{EXPECTED['article_sessions']}")
            if response_counts["total"] < EXPECTED["responses"]:
                incomplete.append(f"逐题回答 {response_counts['total']}/{EXPECTED['responses']}")
            if incomplete:
                issues.append({
                    "severity": "info",
                    "code": "incomplete_expected_counts",
                    "message": "当前数据尚未达到预期正式实验规模：" + "、".join(incomplete) + "。",
                    "count": 1,
                })
        selected_session_ids = self._scope_session_ids(rows)
        completed_participants = {row["participant_id"] for row in rows if row.get("session_status") == "completed"}
        if completed_participants and selected_session_ids:
            placeholders = ",".join("?" for _ in selected_session_ids)
            pref_count = self.db._one(f"SELECT COUNT(DISTINCT s.participant_id) AS count FROM preferences p JOIN sessions s ON s.session_id = p.session_id WHERE p.session_id IN ({placeholders})", selected_session_ids)["count"]
            interview_count = self.db._one(f"SELECT COUNT(DISTINCT s.participant_id) AS count FROM interviews i JOIN sessions s ON s.session_id = i.session_id WHERE i.session_id IN ({placeholders})", selected_session_ids)["count"]
            if pref_count < len(completed_participants):
                issues.append({"severity": "warning", "code": "missing_preferences", "message": "有已完成参与者缺少界面偏好排序。", "count": len(completed_participants) - pref_count})
            if interview_count < len(completed_participants):
                issues.append({"severity": "warning", "code": "missing_interviews", "message": "有已完成参与者缺少半结构化访谈回答。", "count": len(completed_participants) - interview_count})
        observed = {
            "participants": len({row["participant_id"] for row in rows}),
            "article_sessions": len(rows),
            "completed_article_sessions": len(completed_rows),
            "responses": response_counts,
            "surveys": len(workloads),
        }
        return {"expected": EXPECTED, "observed": observed, "issues": issues}
