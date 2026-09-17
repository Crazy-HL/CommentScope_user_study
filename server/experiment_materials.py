"""Load and validate the researcher-authored experiment materials."""
import json
from pathlib import Path

MATERIALS_PATH = Path(__file__).with_name("materials.json")


def load_materials(path=MATERIALS_PATH):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_materials(materials):
    errors = []
    expected = {"A02", "A03", "A04", "A07"}
    if set(materials) != expected:
        errors.append(f"article ids mismatch: {sorted(materials)}")
    for article_id, article in materials.items():
        if not article.get("title") or not article.get("body"):
            errors.append(f"{article_id}: title/body missing")
        comments = article.get("comments", [])
        if len(comments) != 10:
            errors.append(f"{article_id}: expected 10 comments, got {len(comments)}")
        if [c.get("internal_id") for c in comments] != [f"C{i:02d}" for i in range(1, 11)]:
            errors.append(f"{article_id}: comment order/ids invalid")
        for comment in comments:
            for key in ("text", "like_count", "reply_count", "internal_anchor", "position_band"):
                if key not in comment or comment[key] in (None, ""):
                    errors.append(f"{article_id}/{comment.get('internal_id')}: missing {key}")
        groups = article.get("questions", {})
        expected_counts = {"cra": 2, "aca": 2, "ctia": 2}
        for group, count in expected_counts.items():
            items = groups.get(group, [])
            if len(items) != count:
                errors.append(f"{article_id}/{group}: expected {count}, got {len(items)}")
            ids = [item.get("id") for item in items]
            if len(ids) != len(set(ids)):
                errors.append(f"{article_id}/{group}: duplicate question ids")
            for item in items:
                allowed_keys = {"A", "B"} if group == "cra" else {"A", "B", "C", "D"}
                option_keys = {option.get("key") for option in item.get("options", [])}
                if item.get("answer") not in allowed_keys:
                    errors.append(f"{article_id}/{item.get('id')}: invalid {group} answer; expected one of {'/'.join(sorted(allowed_keys))}")
                if len(item.get("options", [])) != (2 if group == "cra" else 4):
                    errors.append(f"{article_id}/{item.get('id')}: invalid option count")
                if option_keys != allowed_keys:
                    errors.append(f"{article_id}/{item.get('id')}: invalid {group} option keys; expected {'/'.join(sorted(allowed_keys))}")
    return errors
