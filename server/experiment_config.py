"""Immutable configuration for the four-condition CommentScope experiment."""
from copy import deepcopy
import re
import unicodedata
from typing import Dict, List


def split_experiment_sentences(text: str) -> List[str]:
    """Split experiment text exactly at the sentence boundaries used by the client.

    The source articles are mostly Chinese, but a few contain Latin punctuation, so
    both Chinese and ASCII sentence terminators are treated as boundaries. Newlines
    are paragraph boundaries and are not included in a sentence.
    """
    if not text:
        return []
    # Protect decimal points before splitting. Otherwise values such as 0.67%
    # become two artificial sentences and an anchored comment lands after
    # ``0.`` instead of beside the complete factual claim.
    protected = re.sub(r"(?<=\d)\.(?=\d)", "\ue000", str(text))
    parts = re.findall(r"[^。！？；.!?\n]+[。！？；.!?]?", protected)
    result = [part.replace("\ue000", ".").strip() for part in parts if part.strip()]
    return result or [str(text).strip()]


def _anchor_fragments(anchor: str) -> List[str]:
    if not anchor:
        return []
    quoted = re.findall(r"[“『「]([^”』」]+)[”』」]", str(anchor))
    value = quoted[0] if quoted else str(anchor)
    value = re.sub(r"^(?:正文)?(?:开头|结尾|首段|后段|文章(?:开头|结尾|后段))", "", value)
    value = re.sub(r"处$", "", value).strip()
    fragments = [part.strip(" ，,。；;：:") for part in re.split(r"(?:……|…{1,}|\.{2,})", value)]
    return [part for part in fragments if len(part) >= 2]


def _normalize_match_text(value: str) -> str:
    """Normalize researcher anchors without changing the sentence splitter.

    Quotes, commas, percentage marks, and full-width punctuation are presentation
    details rather than semantic content. Removing them lets an anchor such as
    “特朗普……收回巴拿马运河” match the sentence containing “收回” in quotes.
    """
    value = unicodedata.normalize("NFKC", str(value or "")).lower()
    return "".join(char for char in value if char.isalnum() or "\u4e00" <= char <= "\u9fff")


def _semantic_tokens(value: str) -> set:
    """Return small, deterministic content tokens for Chinese paraphrase matching."""
    normalized = _normalize_match_text(value)
    if not normalized:
        return set()
    # These function words occur in almost every authored comment and sentence;
    # excluding them keeps the fallback driven by topic words such as 港口、皇帝、
    # 识字率 and 反思 rather than by grammar.
    stopwords = set("的了是和与在有这那一个也都而及其并不没有将把被对为以从中于等着就还又更很最或如果因为所以但是只是然后以及我们你我他她它文章作者认为可以可能就是时候什么这种那个进行相关一些其中并且" )
    chars = [char for char in normalized if char not in stopwords]
    tokens = set(chars)
    tokens.update("".join(chars[index:index + 2]) for index in range(len(chars) - 1))
    tokens.update("".join(chars[index:index + 3]) for index in range(len(chars) - 2))
    return {token for token in tokens if token}


def _semantic_similarity(comment_text: str, sentence: str) -> float:
    comment_tokens = _semantic_tokens(comment_text)
    sentence_tokens = _semantic_tokens(sentence)
    if not comment_tokens or not sentence_tokens:
        return 0.0
    return len(comment_tokens & sentence_tokens) / len(comment_tokens)


def _anchor_resolution(body: str, internal_anchor: str, comment_text: str = ""):
    """Resolve a researcher anchor to a meaningful sentence, without positional guessing."""
    sentences = split_experiment_sentences(body)
    if not sentences:
        return {"index": None, "source": "unlinked", "score": 0.0}

    normalized_sentences = [_normalize_match_text(sentence) for sentence in sentences]
    fragments = [_normalize_match_text(fragment) for fragment in _anchor_fragments(internal_anchor)]
    fragments = [fragment for fragment in fragments if fragment]

    # First choice: all researcher-supplied fragments occur in one sentence.
    exact_candidates = []
    for index, sentence in enumerate(normalized_sentences):
        matched = [fragment for fragment in fragments if fragment in sentence]
        if fragments and len(matched) == len(fragments):
            exact_candidates.append((sum(len(fragment) for fragment in matched), index))
    if exact_candidates:
        _, index = max(exact_candidates, key=lambda item: (item[0], -item[1]))
        return {"index": index, "source": "explicit_anchor", "score": 1.0}

    # Second choice: an anchor may describe a sentence with inserted words or an
    # ellipsis spanning nearby wording. Partial literal coverage is still more
    # trustworthy than any article-position heuristic.
    partial_candidates = []
    for index, sentence in enumerate(normalized_sentences):
        matched_length = sum(len(fragment) for fragment in fragments if fragment in sentence)
        if matched_length:
            coverage = matched_length / sum(len(fragment) for fragment in fragments)
            partial_candidates.append((coverage, matched_length, index))
    if partial_candidates:
        coverage, matched_length, index = max(partial_candidates, key=lambda item: (item[0], item[1], -item[2]))
        if coverage >= 0.25:
            return {"index": index, "source": "explicit_anchor_partial", "score": coverage}

    # Last choice: use the authored comment itself as a transparent semantic
    # fallback. A low-scoring comment remains unlinked instead of being silently
    # placed by comment order or early/middle/late position.
    scored = sorted(
        ((_semantic_similarity(comment_text, sentence), index) for index, sentence in enumerate(sentences)),
        reverse=True,
    )
    if scored:
        best_score, best_index = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        if best_score >= 0.18 and (best_score - second_score >= 0.03 or best_score >= 0.30):
            return {"index": best_index, "source": "semantic_match", "score": best_score}
    return {"index": None, "source": "unlinked", "score": 0.0}


def resolve_anchor_sentence_index(
    body: str,
    internal_anchor: str,
    position_band: str = "middle",
    comment_text: str = "",
):
    """Resolve an authored anchor; ``position_band`` is retained for API compatibility.

    It is deliberately not used as a fallback. Returning ``None`` is safer than
    inventing a sentence when neither the anchor nor the comment has enough
    evidence to establish a relationship.
    """
    del position_band
    return _anchor_resolution(body, internal_anchor, comment_text).get("index")

ARTICLE_IDS = ("A02", "A03", "A04", "A07")
CONDITION_CODES = ("TE", "CS", "SE", "BL")
CONDITION_LABELS = {
    "TE": "Text-End",
    "CS": "Click-to-Show",
    "SE": "Sentence-End",
    "BL": "Between-Line",
}
GROUP_ALLOCATIONS = {
    "S1": {"order": ("A02", "A04", "A03", "A07"), "conditions": {"A02": "TE", "A04": "SE", "A03": "CS", "A07": "BL"}},
    "S2": {"order": ("A04", "A07", "A02", "A03"), "conditions": {"A04": "CS", "A07": "TE", "A02": "BL", "A03": "SE"}},
    "S3": {"order": ("A03", "A02", "A07", "A04"), "conditions": {"A03": "SE", "A02": "BL", "A07": "TE", "A04": "CS"}},
    "S4": {"order": ("A07", "A03", "A04", "A02"), "conditions": {"A07": "BL", "A03": "CS", "A04": "SE", "A02": "TE"}},
    "S5": {"order": ("A03", "A02", "A07", "A04"), "conditions": {"A03": "BL", "A02": "CS", "A07": "SE", "A04": "TE"}},
    "S6": {"order": ("A02", "A04", "A03", "A07"), "conditions": {"A02": "SE", "A04": "BL", "A03": "TE", "A07": "CS"}},
    "S7": {"order": ("A07", "A03", "A04", "A02"), "conditions": {"A07": "CS", "A03": "TE", "A04": "BL", "A02": "SE"}},
    "S8": {"order": ("A04", "A07", "A02", "A03"), "conditions": {"A04": "TE", "A07": "SE", "A02": "CS", "A03": "BL"}},
}
PARTICIPANTS = {}
for i in range(1, 25):
    seq_idx = (i - 1) // 3 + 1
    PARTICIPANTS[f"P{i:02d}"] = f"S{seq_idx}"
STAGE_ORDER = ("instruction", "reading", "cra", "aca", "ctia", "workload")
FINAL_STAGE_ORDER = ("preference", "interview", "complete")
QUESTION_GROUP_ORDER = ("cra", "aca", "ctia")


def build_participant_plan(participant_id: str, materials=None) -> Dict:
    if participant_id not in PARTICIPANTS:
        raise ValueError(f"Unknown participant: {participant_id}")
    if materials is None:
        from experiment_materials import load_materials
        materials = load_materials()
    group_id = PARTICIPANTS[participant_id]
    allocation = GROUP_ALLOCATIONS[group_id]
    articles = [
        {
            "article_id": article_id,
            "article_order": index + 1,
            "condition": allocation["conditions"][article_id],
        }
        for index, article_id in enumerate(allocation["order"])
    ]
    plan = {"participant_id": participant_id, "group_id": group_id, "articles": articles}
    if materials is not None:
        plan["participant_view"] = {
            "participant_id": participant_id,
            "articles": [
                {
                    "article_id": item["article_id"],
                    "article_order": item["article_order"],
                    "title": materials[item["article_id"]]["title"],
                    "body": materials[item["article_id"]]["body"],
                    "comments": [
                        {
                            "text": c["text"],
                            "like_count": c["like_count"],
                            "reply_count": c["reply_count"],
                            "anchor_sentence_index": resolve_anchor_sentence_index(
                                materials[item["article_id"]]["body"],
                                c["internal_anchor"],
                                c["position_band"],
                                c["text"],
                            ),
                        }
                        for c in materials[item["article_id"]]["comments"]
                    ],
                    "questions": {
                        group: [
                            {"id": q["id"], "type": q["type"], "prompt": q["prompt"], "options": deepcopy(q["options"])}
                            for q in materials[item["article_id"]]["questions"][group]
                        ]
                        for group in QUESTION_GROUP_ORDER
                    },
                }
                for item in articles
            ],
        }
    return plan


def validate_allocation(plans: List[Dict]) -> List[str]:
    errors = []
    if len(plans) != 24:
        errors.append(f"expected 24 plans, got {len(plans)}")
    seen = set()
    cell_counts = {(article, condition): 0 for article in ARTICLE_IDS for condition in CONDITION_CODES}
    for plan in plans:
        pid = plan.get("participant_id")
        if pid in seen:
            errors.append(f"duplicate participant {pid}")
        seen.add(pid)
        articles = plan.get("articles", [])
        if len(articles) != 4:
            errors.append(f"{pid}: expected 4 articles")
        if {a.get("article_id") for a in articles} != set(ARTICLE_IDS):
            errors.append(f"{pid}: article set is not complete")
        if {a.get("condition") for a in articles} != set(CONDITION_CODES):
            errors.append(f"{pid}: conditions are not one-each")
        for item in articles:
            cell = (item.get("article_id"), item.get("condition"))
            if cell in cell_counts:
                cell_counts[cell] += 1
            else:
                errors.append(f"{pid}: invalid allocation {cell}")
    for cell, count in cell_counts.items():
        if count != 6:
            errors.append(f"{cell}: expected 6, got {count}")
    return errors
