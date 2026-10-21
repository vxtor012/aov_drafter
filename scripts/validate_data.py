"""Validate the hero snapshot and its embedded JavaScript copy (stdlib only)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"Top", "Jungle", "Mid", "AD", "SP"}
TIERS = {"S+", "S", "A", "B", "C"}
ATTRIBUTES = {"damage", "tankiness", "mobility", "teamfight", "split_push"}


def validate_database(heroes):
    if not isinstance(heroes, list) or not heroes:
        raise ValueError("Hero database must be a non-empty list")
    ids = [h["id"] for h in heroes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate hero IDs")
    known = set(ids)
    for hero in heroes:
        hid = hero["id"]
        if not isinstance(hid, str) or not hid.isalnum() or hid != hid.lower():
            raise ValueError(f"Invalid ID: {hid}")
        if not hero["name"] or not isinstance(hero["avatar"], str):
            raise ValueError(f"Missing display data: {hid}")
        if hero["main_role"] not in ROLES or hero["tier"] not in TIERS:
            raise ValueError(f"Invalid role/tier: {hid}")
        roles = hero.get("roles")
        if not isinstance(roles, list) or not roles or roles[0] != hero["main_role"] or len(roles) != len(set(roles)) or any(role not in ROLES for role in roles):
            raise ValueError(f"Invalid supported roles: {hid}")
        if not isinstance(hero.get("meta_snapshot"), str) or not isinstance(hero.get("meta_source"), str):
            raise ValueError(f"Missing meta provenance: {hid}")
        for key in ("win_rate", "pick_rate", "ban_rate"):
            value = hero[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError(f"Invalid {key}: {hid}")
        for key in ATTRIBUTES:
            value = hero["attributes"][key]
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise ValueError(f"Invalid attribute {key}: {hid}")
        seen = set()
        for counter in hero["counters"]:
            cid = counter["id"]
            if cid not in known or cid == hid or cid in seen or not isinstance(counter["reason"], str):
                raise ValueError(f"Invalid counter {cid}: {hid}")
            seen.add(cid)
        if not isinstance(hero["tags"], list):
            raise ValueError(f"Invalid tags: {hid}")
    return heroes


def main():
    heroes = json.loads((ROOT / "data" / "crawled_heroes.json").read_text(encoding="utf-8"))
    validate_database(heroes)
    js = (ROOT / "public" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    marker = "const HERO_DATABASE = "
    if js.count(marker) != 1:
        raise ValueError("Expected exactly one HERO_DATABASE")
    embedded, _ = json.JSONDecoder().raw_decode(js.split(marker, 1)[1])
    if embedded != heroes:
        raise ValueError("app.js and crawled_heroes.json are out of sync")
    print(f"OK: {len(heroes)} heroes, {sum(len(h['counters']) for h in heroes)} counter links; JSON/JS synchronized")


if __name__ == "__main__":
    main()
