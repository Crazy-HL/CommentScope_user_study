import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiment_config import (  # noqa: E402
    PARTICIPANTS,
    GROUP_ALLOCATIONS,
    ARTICLE_IDS,
    CONDITION_CODES,
    build_participant_plan,
    validate_allocation,
)
from experiment_materials import load_materials, validate_materials  # noqa: E402


def test_all_24_participants_are_preconfigured_and_balanced():
    assert list(PARTICIPANTS) == [f"P{i:02d}" for i in range(1, 25)]
    plans = [build_participant_plan(pid) for pid in PARTICIPANTS]
    assert len({p["group_id"] for p in plans}) == 4
    assert all(len(p["articles"]) == 4 for p in plans)
    assert validate_allocation(plans) == []

    cells = {(article_id, condition): 0 for article_id in ARTICLE_IDS for condition in CONDITION_CODES}
    for plan in plans:
        for item in plan["articles"]:
            cells[(item["article_id"], item["condition"])] += 1
    assert set(cells.values()) == {6}


def test_materials_contract_is_complete_and_has_unique_answers():
    materials = load_materials()
    errors = validate_materials(materials)
    assert errors == []
    assert set(materials) == set(ARTICLE_IDS)
    for article in materials.values():
        assert len(article["comments"]) == 10
        assert len(article["questions"]["cra"]) == 4
        assert len(article["questions"]["aca"]) == 2
        assert len(article["questions"]["ctia"]) == 2
        assert len(article["questions"]["location"]) == 2
        assert all("answer" in item for group in article["questions"].values() for item in group)


def test_participant_payload_does_not_include_researcher_only_fields():
    plan = build_participant_plan("P01")
    assert "group_id" not in plan["participant_view"]
    for article in plan["participant_view"]["articles"]:
        assert "condition" not in article
        assert "answer" not in article
        assert "internal_anchor" not in article
        for comment in article["comments"]:
            assert "position_band" not in comment
        for question_group in article["questions"].values():
            for item in question_group:
                assert "answer" not in item
                assert "internal_comment_id" not in item


def test_cra_questions_are_strictly_binary_appearance_choices():
    materials = load_materials()
    materials["A02"]["questions"]["cra"][0]["options"][1]["key"] = "C"
    errors = validate_materials(materials)
    assert any("A/B" in error and "/R1" in error for error in errors)


def test_sentence_splitter_keeps_decimal_numbers_in_one_sentence():
    from experiment_config import split_experiment_sentences

    sentences = split_experiment_sentences("到了1908年，全国百姓的识字率仅仅只有0.67%。这样的国情，百姓怎么睁眼看世界？")

    assert sentences == [
        "到了1908年，全国百姓的识字率仅仅只有0.67%。",
        "这样的国情，百姓怎么睁眼看世界？",
    ]


def test_comment_anchors_resolve_to_real_sentence_indices_without_exposing_anchor_text():
    from experiment_config import resolve_anchor_sentence_index, split_experiment_sentences

    materials = load_materials()
    for article in materials.values():
        sentences = split_experiment_sentences(article["body"])
        assert len(sentences) > 3
        for comment in article["comments"]:
            index = resolve_anchor_sentence_index(
                article["body"], comment["internal_anchor"], comment["position_band"], comment["text"]
            )
            assert 0 <= index < len(sentences), (article["article_id"], comment["internal_id"], index)

    assert resolve_anchor_sentence_index(
        materials["A03"]["body"], materials["A03"]["comments"][0]["internal_anchor"], "early"
    ) == 0
    assert resolve_anchor_sentence_index(
        materials["A04"]["body"], materials["A04"]["comments"][3]["internal_anchor"], "middle"
    ) >= 1


def test_curated_anchors_use_literal_evidence_for_each_weak_match():
    from experiment_config import _anchor_resolution

    materials = load_materials()
    expected = {
        ("A02", "C06"): 50,
        ("A03", "C10"): 74,
        ("A04", "C07"): 42,
        ("A04", "C09"): 52,
        ("A07", "C06"): 23,
        ("A07", "C08"): 27,
    }
    for (article_id, comment_id), expected_index in expected.items():
        article = materials[article_id]
        comment = next(item for item in article["comments"] if item["internal_id"] == comment_id)
        resolution = _anchor_resolution(article["body"], comment["internal_anchor"], comment["text"])
        assert resolution["index"] == expected_index
        assert resolution["source"] == "explicit_anchor"


def test_anchor_resolution_uses_researcher_anchor_or_comment_semantics_not_position_band():
    from experiment_config import resolve_anchor_sentence_index

    materials = load_materials()
    # These anchors intentionally use punctuation, inserted words, or an ellipsis
    # that do not survive a literal substring lookup. They must still resolve to
    # the sentence carrying the referenced idea, not to a position-band fallback.
    assert resolve_anchor_sentence_index(
        materials["A03"]["body"],
        materials["A03"]["comments"][9]["internal_anchor"],
        "early",
        materials["A03"]["comments"][9]["text"],
    ) == 74
    assert resolve_anchor_sentence_index(
        materials["A07"]["body"],
        materials["A07"]["comments"][7]["internal_anchor"],
        "early",
        materials["A07"]["comments"][7]["text"],
    ) == 27


def test_unrelated_anchor_is_not_assigned_by_position_band():
    from experiment_config import resolve_anchor_sentence_index

    assert resolve_anchor_sentence_index(
        "甲。乙。丙。",
        "“不存在的锚点”处",
        "late",
        "这条评论与文章句子没有共同的内容。",
    ) is None


def test_participant_comments_include_deidentified_anchor_sentence_index():
    article = build_participant_plan("P01")["participant_view"]["articles"][0]
    for comment in article["comments"]:
        assert isinstance(comment["anchor_sentence_index"], int)
        assert "internal_anchor" not in comment
        assert "internal_id" not in comment
