#!/usr/bin/env python3
"""
Collector — Provinciale Staten voting overview.

Pulls per-party voting records per province, unions them into one motie list, and writes a
normalized data/<province>.json that the static site reads, plus a data/provinces.json index.

Multi-province / multi-vendor: each province in PROVINCES names a `vendor`, dispatched to an
adapter in ADAPTERS. Currently only the GemeenteOplossingen ("go") adapter is implemented
(Utrecht). iBabs / Notubiz adapters are TODO — see ../provinces.md.

Zero dependencies (stdlib only) so GitHub Actions needs no install step.
See ../data-sources.md for the reverse-engineered GO endpoints.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, date, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --- Province registry --------------------------------------------------------
# Each entry: key, name, vendor, base, term_start (y,m,d), term_label, style, license.
# Add a province here once its vendor adapter exists (see ../provinces.md for the map).
PROVINCES = [
    {
        "key": "utrecht",
        "name": "Utrecht",
        "vendor": "go",
        "base": "https://www.stateninformatie.provincie-utrecht.nl",
        "term_start": (2023, 3, 29),   # PS election 29 March 2023
        "term_label": "2023-2027",
        "style": {"accent": "#EC0000", "headerBg": "#1b1b1b"},
        "license": "Open data - Provincie Utrecht / Statengriffie",
    },
]

# Bodies that are type "Fractie" in the GO API but are not voting parties.
NOT_A_PARTY = {"Gedeputeerde Staten"}

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


# --- GemeenteOplossingen (GO) adapter ----------------------------------------
def collect_go(p):
    """Return {parties, moties} for a GO province, or None if it has no votes endpoint."""
    base = p["base"].rstrip("/")
    api = base + "/api/v2"
    term_start = date(*p["term_start"])
    mcache = {}

    def meeting_date(mid):
        if mid in mcache:
            return mcache[mid]
        d = None
        data = try_json(f"{api}/meetings/{mid}")
        if data and data.get("result", {}).get("meeting"):
            d = data["result"]["meeting"].get("date")
        mcache[mid] = d
        time.sleep(SLEEP)
        return d

    gdata = try_json(f"{api}/groups?limit=100")
    if not gdata or "result" not in gdata:
        return None
    parties = [{"name": g["name"], "slug": slugify(g["name"]), "sortOrder": g.get("sortOrder", 999)}
               for g in gdata["result"]["groups"]
               if g.get("type") == "Fractie" and g["name"] not in NOT_A_PARTY]
    print(f"  candidate parties: {len(parties)}")

    moties = {}
    parties_with_data = {}
    for party in parties:
        data = try_json(f"{base}/Samenstelling/{party['slug']}/votings")
        time.sleep(SLEEP)
        items_by_year = data.get("items") if data else None
        if not isinstance(items_by_year, dict):   # empty result is [] not {}, or 404
            continue
        kept = 0
        for year, items in items_by_year.items():
            if int(year) < term_start.year:
                continue
            for it in items:
                mid = it["meetingId"]
                mdate = meeting_date(mid) or it.get("updatedAt", {}).get("date", "")[:10]
                try:
                    d = datetime.strptime(mdate[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if d < term_start:
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
                        # Human-facing page (301-redirects to the pretty agenda-item URL).
                        "source": (f"{base}/vergaderingen/document/{it['documentId']}" if it.get("documentId")
                                   else f"{base}/vergaderingen/agendapunt/{it['meetingItemId']}" if it.get("meetingItemId")
                                   else f"{base}/vergaderingen/{mid}"),
                        "votes": {},
                    }
                vc = (it.get("voteResult") or {}).get("voteCounts", {})
                moties[vid]["votes"][party["slug"]] = {
                    "agree": vc.get("agree", 0),
                    "disagree": vc.get("disagree", 0),
                    "abstain": vc.get("abstain", 0),
                }
                kept += 1
        if kept:
            parties_with_data[party["slug"]] = party

    motie_list = sorted(moties.values(), key=lambda m: (m["date"], m["title"]), reverse=True)
    for m in motie_list:
        m["totals"] = {"agree": sum(v["agree"] for v in m["votes"].values()),
                       "disagree": sum(v["disagree"] for v in m["votes"].values())}
    columns = sorted(parties_with_data.values(), key=lambda x: x["sortOrder"])
    return {"parties": [{"slug": x["slug"], "name": x["name"]} for x in columns], "moties": motie_list}


ADAPTERS = {"go": collect_go}


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    for p in PROVINCES:
        print(f"== {p['name']} ({p['vendor']}) ==")
        adapter = ADAPTERS.get(p["vendor"])
        res = None
        if adapter:
            try:
                res = adapter(p)
            except Exception as e:
                print(f"  ERROR: {e}")
        available = bool(res and res["moties"])
        if available:
            out = {
                "meta": {
                    "province": p["name"],
                    "body": "Provinciale Staten",
                    "term": p["term_label"],
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "source": p["base"],
                    "license": p.get("license", ""),
                    "style": p.get("style", {}),
                    "counts": {"moties": len(res["moties"]), "parties": len(res["parties"])},
                },
                "parties": res["parties"],
                "moties": res["moties"],
            }
            (DATA_DIR / f"{p['key']}.json").write_text(
                json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            by_type = {}
            for m in res["moties"]:
                by_type[m["type"]] = by_type.get(m["type"], 0) + 1
            print(f"  wrote {p['key']}.json: {len(res['moties'])} moties, "
                  f"{len(res['parties'])} parties, {by_type}")
        else:
            print("  (no data — marked unavailable)")
        index.append({"key": p["key"], "name": p["name"], "available": available})

    (DATA_DIR / "provinces.json").write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "default": next((i["key"] for i in index if i["available"]), None),
         "provinces": index},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote provinces.json: available = {[i['key'] for i in index if i['available']]}")


if __name__ == "__main__":
    sys.exit(main())
