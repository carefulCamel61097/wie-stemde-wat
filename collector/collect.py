#!/usr/bin/env python3
"""
Collector — Provinciale Staten Utrecht voting overview (GO adapter).

Pulls per-party voting records from the GemeenteOplossingen platform behind
stateninformatie.provincie-utrecht.nl, unions them into one motie list, and writes a
normalized data/utrecht.json that the static site reads.

Zero dependencies (stdlib only) so GitHub Actions needs no install step.

See ../data-sources.md for the reverse-engineered endpoints.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timezone
from pathlib import Path

BASE = "https://www.stateninformatie.provincie-utrecht.nl"
API = BASE + "/api/v2"

# Current term started with the PS election of 29 March 2023.
TERM_START = date(2023, 3, 29)
TERM_LABEL = "2023-2027"

# Bodies that are type "Fractie" in the API but are not voting parties.
NOT_A_PARTY = {"Gedeputeerde Staten"}

OUT = Path(__file__).resolve().parent.parent / "data" / "utrecht.json"

HEADERS = {
    "User-Agent": "wie-stemde-wat collector (open-data overview; contact via GitHub)",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
}
SLEEP = 0.3  # be polite between requests


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def try_json(url):
    """GET that tolerates 4xx/5xx (some party slugs 500); returns None on failure."""
    try:
        return get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None


def slugify(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)   # drop punctuation (e.g. "UtrechtNu!" -> "utrechtnu")
    s = re.sub(r"\s+", "-", s.strip())
    return s


def classify(title):
    """Two naming schemes exist: word form ("Motie 97", "Amendement 19") and code form
    ("M26-40a", "A26-12"). Handle both."""
    low = title.strip().lower()
    if "ordevoorstel" in low or "orde voorstel" in low:
        return "ordevoorstel"
    if "amendement" in low or re.match(r"^a\s*\d", low):
        return "amendement"
    if "motie" in low or re.match(r"^m\s*\d", low):
        return "motie"
    if low.startswith("sv") or "statenvoorstel" in low or "besluit" in low:
        return "besluit"
    return "overig"


def fetch_parties():
    """Authoritative party list from the API, slugified to site slugs."""
    data = get_json(f"{API}/groups?limit=100")
    parties = []
    for g in data["result"]["groups"]:
        if g.get("type") != "Fractie" or g["name"] in NOT_A_PARTY:
            continue
        parties.append({
            "name": g["name"],
            "slug": slugify(g["name"]),
            "sortOrder": g.get("sortOrder", 999),
        })
    return parties


_meeting_cache = {}


def meeting_date(meeting_id):
    if meeting_id in _meeting_cache:
        return _meeting_cache[meeting_id]
    d = None
    data = try_json(f"{API}/meetings/{meeting_id}")
    if data and data.get("result", {}).get("meeting"):
        d = data["result"]["meeting"].get("date")
    _meeting_cache[meeting_id] = d
    time.sleep(SLEEP)
    return d


def main():
    parties = fetch_parties()
    print(f"Candidate parties from API: {len(parties)}")

    moties = {}            # votingId -> motie record
    parties_with_data = {} # slug -> party meta (only those with current-term votes)

    for p in parties:
        url = f"{BASE}/Samenstelling/{p['slug']}/votings"
        data = try_json(url)
        time.sleep(SLEEP)
        items_by_year = data.get("items") if data else None
        if not isinstance(items_by_year, dict):   # empty result is [] not {}
            print(f"  - {p['slug']:<28} no data (skip)")
            continue

        kept = 0
        for year, items in items_by_year.items():
            if int(year) < TERM_START.year:
                continue
            for it in items:
                mid = it["meetingId"]
                mdate = meeting_date(mid) or it.get("updatedAt", {}).get("date", "")[:10]
                try:
                    d = datetime.strptime(mdate[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if d < TERM_START:
                    continue

                vid = it["votingId"]
                if vid not in moties:
                    moties[vid] = {
                        "id": vid,
                        "documentId": it.get("documentId"),
                        "meetingItemId": it.get("meetingItemId"),
                        "meetingId": mid,
                        "date": mdate[:10],
                        "title": it["description"],
                        "type": classify(it["description"]),
                        "result": (it.get("voteResult") or {}).get("name"),
                        "resultLabel": (it.get("voteResult") or {}).get("label"),
                        "source": f"{BASE}/vergaderingen/stemmingen/document/{it.get('documentId')}",
                        "votes": {},
                    }
                vc = (it.get("voteResult") or {}).get("voteCounts", {})
                moties[vid]["votes"][p["slug"]] = {
                    "agree": vc.get("agree", 0),
                    "disagree": vc.get("disagree", 0),
                    "abstain": vc.get("abstain", 0),
                }
                kept += 1

        if kept:
            parties_with_data[p["slug"]] = p
            print(f"  + {p['slug']:<28} {kept} votes")
        else:
            print(f"  - {p['slug']:<28} no current-term votes (skip)")

    # Overall totals = sum across present parties (absent members not counted).
    motie_list = sorted(moties.values(), key=lambda m: (m["date"], m["title"]), reverse=True)
    for m in motie_list:
        agree = sum(v["agree"] for v in m["votes"].values())
        disagree = sum(v["disagree"] for v in m["votes"].values())
        m["totals"] = {"agree": agree, "disagree": disagree}

    columns = sorted(parties_with_data.values(), key=lambda p: p["sortOrder"])
    out = {
        "meta": {
            "province": "Utrecht",
            "body": "Provinciale Staten",
            "term": TERM_LABEL,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": BASE,
            "license": "Open data - Provincie Utrecht / Statengriffie",
            # Province house style (huisstijl) — drives the site theme. Per-province for v2.
            "style": {"accent": "#EC0000", "headerBg": "#1b1b1b"},
            "counts": {"moties": len(motie_list), "parties": len(columns)},
        },
        "parties": [{"slug": p["slug"], "name": p["name"]} for p in columns],
        "moties": motie_list,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    by_type = {}
    for m in motie_list:
        by_type[m["type"]] = by_type.get(m["type"], 0) + 1
    print(f"\nWrote {OUT}")
    print(f"  parties (columns): {len(columns)} -> {[p['slug'] for p in columns]}")
    print(f"  moties total: {len(motie_list)}")
    print(f"  by type: {by_type}")
    print(f"  date range: {motie_list[-1]['date']} .. {motie_list[0]['date']}" if motie_list else "  (no moties)")


if __name__ == "__main__":
    sys.exit(main())
