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
    {
        "key": "noord-holland",
        "name": "Noord-Holland",
        "vendor": "ibabs",
        "base": "https://noordholland.bestuurlijkeinformatie.nl",
        "report": "84a8ac43-1424-48a9-8a1a-0c0bbcdfd8ed",   # iBabs "Moties" report GUID
        "term_start": (2023, 3, 29),   # PS election 15 March 2023
        "term_label": "2023-2027",
        "style": {"accent": "#2891e0", "headerBg": "#0e2438"},   # NH portal huisstijl blue
        "license": "Open data - Provincie Noord-Holland (iBabs publieksportaal)",
        # iBabs scope: the portal's register lists adopted moties only, and votes are recorded
        # per fractie (not per member), so "ruwe getallen" show 1–0 rather than seat counts.
        "note": "De bron (iBabs-motieregister) bevat alleen aangenomen moties; stemmen zijn "
                "op fractieniveau geregistreerd, dus zonder exacte aantallen per fractie.",
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


def http(url, data=None, ctype=None):
    """GET, or POST when `data` (a form string) is given. Returns the decoded body."""
    headers = dict(HEADERS)
    if ctype:
        headers["Content-Type"] = ctype
    body = data.encode("utf-8") if isinstance(data, str) else data
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def get_json(url):
    return json.loads(http(url))


def try_json(url):
    """GET that tolerates 4xx/5xx (some party slugs 500); returns None on failure."""
    try:
        return get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None


def try_text(url):
    """GET returning text (HTML), tolerant of network/HTTP errors."""
    try:
        return http(url)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None


def post_json(url, body):
    """POST a form body and parse the JSON response; None on failure."""
    try:
        return json.loads(http(url, data=body, ctype="application/x-www-form-urlencoded"))
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


# --- iBabs adapter ------------------------------------------------------------
# The iBabs publieksportaal ({prov}.bestuurlijkeinformatie.nl) is an ASP.NET SPA with a
# DataTables "Moties" report. Per-fractie votes are recoverable without auth (data-sources.md §7):
#   POST /Reports/GetReportData/{guid}  -> clean JSON motie list (DT_RowId, motienummer, ...)
#   GET  /Reports/Item/{DT_RowId}       -> server-rendered HTML; the "Stemverhouding" field
#                                          holds the per-fractie outcome as FREE TEXT, e.g.
#       "Tegen: VVD /BBB /JA21. Voor: overige fracties (Fractie De Weerdt afwezig)."
# Granularity is faction-level only (no member counts) -> store agree/disagree as 1/0; the
# frontend's "ruwe getallen"/split-vote features degrade gracefully for iBabs provinces.
#
# Parsing strategy: the losing side is usually named and the winning side is "overige fracties"
# (= everyone else). To expand "overige fracties" we need the term's party universe; we build it
# data-driven (pass 1: collect every explicitly-named fractie across all in-term moties), then
# resolve each motie (pass 2). Composition changes per term, so we term-scope first via "Datum PS".

# Normalize fractie spellings to one canonical display name. Keys are lowercased; multi-word
# keys let the greedy tokenizer split space-separated lists ("PVV FvD") without breaking
# multi-word party names ("Fractie De Weerdt"). Unknown tokens pass through verbatim, so the
# adapter also works for the other iBabs provinces (Limburg, Noord-Brabant, Zeeland).
IBABS_ALIASES = {
    "gl": "GroenLinks", "groenlinks": "GroenLinks", "groen links": "GroenLinks",
    "pvda": "PvdA", "partij van de arbeid": "PvdA",
    "pvdd": "PvdD", "partij voor de dieren": "PvdD",
    "cu": "ChristenUnie", "christenunie": "ChristenUnie", "christen unie": "ChristenUnie",
    "cda": "CDA", "d66": "D66", "vvd": "VVD", "bbb": "BBB", "sp": "SP",
    "pvv": "PVV", "ja21": "JA21", "ja 21": "JA21", "volt": "Volt",
    "fvd": "FvD", "forum voor democratie": "FvD",
    "50plus": "50PLUS", "50 plus": "50PLUS", "denk": "DENK", "sgp": "SGP",
    "fractie de weerdt": "Fractie De Weerdt", "de weerdt": "Fractie De Weerdt",
}
# A whole side phrased as these means "everyone present" (no opposing side).
IBABS_ALL = ("unaniem", "alle fracties", "alle partijen")
# Filler words to skip when splitting a space-separated list (label words / stopwords).
IBABS_SKIP = {"fractie", "fracties", "frct.", "frc.", "frct", "frc", "de", "en", "het"}


def ibabs_canon(token):
    """Canonical display name for one fractie token, or None if empty."""
    t = re.sub(r"\s+", " ", token or "").strip().strip(".,;:").strip()
    if not t or t.isdigit() or len(t) < 2:   # drop vote-count numerals / stray single chars
        return None
    low = t.lower()
    if low in IBABS_ALIASES:
        return IBABS_ALIASES[low]
    # strip a leading "fractie"/"frct." label (e.g. "fractie FvD" -> "FvD")
    m = re.match(r"(?:fracties?|frct\.?|frc\.?)\s+(.+)$", t, re.I)
    if m and m.group(1).strip().lower() != low:
        return ibabs_canon(m.group(1))
    return t


def ibabs_greedy(text):
    """Tokenize a space-separated side ("PVV FvD") into canonical names, longest-alias-first
    so multi-word names stay intact."""
    words = text.split()
    out, i = [], 0
    while i < len(words):
        hit = False
        for L in range(min(4, len(words) - i), 0, -1):
            cand = " ".join(words[i:i + L]).lower().strip(".,;:")
            if cand in IBABS_ALIASES:
                out.append(IBABS_ALIASES[cand]); i += L; hit = True; break
        if not hit:
            if words[i].lower().strip(".,;:") in IBABS_SKIP:
                i += 1; continue
            c = ibabs_canon(words[i])
            if c:
                out.append(c)
            i += 1
    return out


def ibabs_parties(text):
    """Parse one side's fractie list. Separators vary (',', '/', ' / ', ' en ', or just space)."""
    text = re.sub(r"\s+", " ", text or "").strip(" .")
    if not text:
        return []
    if "/" in text or "," in text:
        chunks = text.replace("/", ",").split(",")
        return [c for c in (ibabs_canon(x) for x in chunks) if c]
    if re.search(r"\sen\s", text, re.I):
        return [c for c in (ibabs_canon(x) for x in re.split(r"\sen\s", text, flags=re.I)) if c]
    return ibabs_greedy(text)


def ibabs_parse(raw):
    """Parse a Stemverhouding string into (voor_spec, tegen_spec, afwezig_set, split_set), or
    None when there is no usable vote (withdrawn/postponed/blank). Each *_spec is one of:
      ("list", {names}) | ("rest", None) | ("all", None) | None.
    The free text is messy: labels sometimes glue to a preceding name ("PvdAVoor:") and a
    "Verdeeld gestemd:" clause marks fracties that split their own vote."""
    t = re.sub(r"\s+", " ", raw or "").strip()
    if not t or t.lower() in ("nvt", "n.v.t.", "aangehouden", "aangehouden.", "vervallen", "ingetrokken"):
        return None
    # Un-glue labels stuck to a preceding word: "SPVerdeeld gestemd:" / "PvdAVoor:".
    t = re.sub(r"(?i)(?<=\w)(verdeeld\s+gestemd\s*:)", r" \1", t)
    t = re.sub(r"(?i)(?<=[A-Za-z])(voor|tegen|afwezig)\s*:", r" \1:", t)

    afwezig, split_set = set(), set()

    def grab_parens(s):
        # "(Fractie De Weerdt afwezig)" / "(CU-SGP/Boer afwezig)" -> absent fracties
        for m in re.finditer(r"\(([^)]*)\)", s):
            inner = m.group(1)
            if "afwezig" in inner.lower():
                for p in ibabs_parties(re.sub(r"afwezig", "", inner, flags=re.I)):
                    afwezig.add(p)
        return re.sub(r"\([^)]*\)", " ", s)

    t = grab_parens(t)
    labels = list(re.finditer(r"(?i)\b(voor|tegen|afwezig|verdeeld(?:\s+gestemd)?)\s*:", t))
    if not labels:
        if any(w in t.lower() for w in IBABS_ALL):
            return (("all", None), None, afwezig, split_set)
        return None

    voor_spec = tegen_spec = None
    for i, m in enumerate(labels):
        key = m.group(1).lower()
        end = labels[i + 1].start() if i + 1 < len(labels) else len(t)
        seg = t[m.end():end].strip(" .")
        seglow = seg.lower()
        if key == "afwezig":
            afwezig.update(ibabs_parties(seg))
            continue
        if key.startswith("verdeeld"):   # fracties that split their own vote
            split_set.update(ibabs_parties(seg))
            continue
        if any(w in seglow for w in IBABS_ALL):
            spec = ("all", None)
        elif "overige" in seglow:
            spec = ("rest", None)
        else:
            spec = ("list", set(ibabs_parties(seg)))
        if key == "voor":
            voor_spec = spec
        else:
            tegen_spec = spec
    return (voor_spec, tegen_spec, afwezig, split_set)


def ibabs_resolve(voor_spec, tegen_spec, afwezig, split, universe):
    """Turn the parsed specs into concrete (voor_set, tegen_set, split_set), expanding "overige
    fracties" / "unaniem" against the term's party universe minus absentees and split voters."""
    split = split - afwezig
    present = universe - afwezig - split
    listed = lambda s: set(s[1]) if s and s[0] == "list" else set()
    voor, tegen = listed(voor_spec), listed(tegen_spec)
    if voor_spec and voor_spec[0] == "all":
        voor = present - tegen
    if tegen_spec and tegen_spec[0] == "all":
        tegen = present - voor
    if voor_spec and voor_spec[0] == "rest":
        voor = present - tegen
    if tegen_spec and tegen_spec[0] == "rest":
        tegen = present - voor
    voor -= afwezig | split
    tegen -= afwezig | split
    voor -= tegen   # a party can't be on both sides
    return voor, tegen, split


def ibabs_date(s):
    m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", (s or "").strip())
    if not m:
        return None
    dd, mm, yy = map(int, m.groups())
    try:
        return date(yy, mm, dd)
    except ValueError:
        return None


def ibabs_field(html, label):
    """Pull a <dt>Label</dt><dd>VALUE</dd> pair out of the detail page; tags stripped."""
    m = re.search(r"<dt[^>]*>\s*" + re.escape(label) + r"\s*</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.S)
    if not m:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()


def ibabs_id(r):
    """Stable numeric id (the frontend coerces dataset ids with +; GUIDs would become NaN)."""
    ident = str(r.get("identity") or "").strip()
    if ident.isdigit():
        return int(ident)
    return int(r["DT_RowId"].replace("-", "")[:12], 16)


def ibabs_result(status):
    s = (status or "").lower()
    if s.startswith("aangenomen"):
        return "accepted"
    if s.startswith("verworpen"):
        return "rejected"
    return s or None


def ibabs_title(r):
    title = (r.get("title") or "").strip()
    num = (r.get("motienummer") or "").strip()
    if num and num.lower() not in title.lower():
        return f"{num} — {title}" if title else num
    return title


def collect_ibabs(p):
    """Return {parties, moties} for an iBabs province, or None if the report is unreachable."""
    base = p["base"].rstrip("/")
    guid = p["report"]
    term_start = date(*p["term_start"])

    listing = post_json(f"{base}/Reports/GetReportData/{guid}", "draw=1&start=0&length=2000")
    rows = listing.get("data") if isinstance(listing, dict) else None
    if not rows:
        return None

    # Pre-filter by indiening year to avoid fetching hundreds of pre-term detail pages; the real
    # term cut is applied on each motie's "Datum PS" below (a 1-year margin covers late-indiened votes).
    cand = []
    for r in rows:
        try:
            yr = int(str(r.get("ingediendindatum", ""))[-4:])
        except ValueError:
            yr = 0
        if yr >= term_start.year - 1:
            cand.append(r)
    print(f"  report rows: {len(rows)}; candidates (ingediend >= {term_start.year - 1}): {len(cand)}")

    # Fetch each candidate's detail page, parse its Stemverhouding, keep the in-term ones.
    parsed = []
    skipped = 0
    for r in cand:
        html = try_text(f"{base}/Reports/Item/{r['DT_RowId']}")
        time.sleep(SLEEP)
        if not html:
            skipped += 1
            continue
        d = ibabs_date(ibabs_field(html, "Datum PS") or r.get("ingediendindatum"))
        if not d or d < term_start:
            continue
        parsed.append((r, d, ibabs_parse(ibabs_field(html, "Stemverhouding"))))
    if skipped:
        print(f"  WARN: {skipped} detail page(s) failed to fetch")

    # Pass 1: build the term's party universe from every explicitly-named fractie, and record
    # each fractie's earliest "present" date. Composition shifts WITHIN a term (e.g. a mid-term
    # splinter), so a fractie may only join "overige fracties" from when it first exists. We date
    # that from explicit-presence signals — named on a side, noted afwezig, or listed as indiener
    # — which catch established parties at term start but a splinter only once it appears. (We do
    # NOT use "overige" itself as a signal: that's exactly what we're gating.)
    universe = set()
    first_seen = {}

    def mark(party, d):
        if party and (party not in first_seen or d < first_seen[party]):
            first_seen[party] = d

    for r, d, spec in parsed:
        if not spec:
            continue
        voor_spec, tegen_spec, afwezig, split = spec
        explicit = set(afwezig) | set(split)
        for s in (voor_spec, tegen_spec):
            if s and s[0] == "list":
                explicit |= s[1]
        universe |= explicit
        for party in explicit | set(ibabs_parties(r.get("fracties", ""))):
            mark(party, d)

    # Pass 2: resolve each motie's votes against the fracties that already existed on its date.
    moties, appear, name_by_slug = [], {}, {}
    no_votes = 0
    for r, d, spec in parsed:
        if not spec:
            no_votes += 1
            continue
        present_universe = {p for p in universe if first_seen.get(p, term_start) <= d}
        voor, tegen, split = ibabs_resolve(*spec, present_universe)
        if not voor and not tegen and not split:
            no_votes += 1
            continue
        votes = {}
        # split (= "verdeeld gestemd") -> agree==disagree, which the frontend renders as "O" + split dot.
        tagged = [(x, 1, 0) for x in voor] + [(x, 0, 1) for x in tegen] + [(x, 1, 1) for x in split]
        for party, agree, disagree in tagged:
            slug = slugify(party)
            name_by_slug[slug] = party
            votes[slug] = {"agree": agree, "disagree": disagree, "abstain": 0}
            appear[slug] = appear.get(slug, 0) + 1
        status = (r.get("status") or "").strip()
        moties.append({
            "id": ibabs_id(r),
            "date": d.isoformat(),
            "title": ibabs_title(r),
            "type": "motie",   # the report is "Moties"; classify() would just return "overig"
            "result": ibabs_result(status),
            "resultLabel": status or None,
            "source": f"{base}/Reports/Item/{r['DT_RowId']}",
            "votes": votes,
        })
    print(f"  in-term moties with votes: {len(moties)} (no parseable vote: {no_votes}); "
          f"universe: {len(appear)} fracties")

    moties.sort(key=lambda m: (m["date"], m["title"]), reverse=True)
    for m in moties:
        m["totals"] = {"agree": sum(1 for v in m["votes"].values() if v["agree"] > v["disagree"]),
                       "disagree": sum(1 for v in m["votes"].values() if v["disagree"] > v["agree"])}
    # Columns ordered by how often a fractie appears (most active first), then by name.
    order = sorted(appear, key=lambda s: (-appear[s], name_by_slug[s].lower()))
    return {"parties": [{"slug": s, "name": name_by_slug[s]} for s in order], "moties": moties}


ADAPTERS = {"go": collect_go, "ibabs": collect_ibabs}


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
                    "note": p.get("note", ""),
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
