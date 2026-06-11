#!/usr/bin/env python3
"""
Collector — Provinciale Staten voting overview.

Pulls per-party voting records per scope, unions them into one motie list, and writes a
normalized data/<scope>.json that the static site reads, plus a data/catalog.json index that
groups scopes by category (Tweede Kamer / Provinciale Staten) for the "pick category -> scope" UX.

Multi-vendor / multi-category: each entry in SOURCES names a `vendor`, dispatched to an adapter
in ADAPTERS (go = GemeenteOplossingen, ibabs, tk = Tweede Kamer OData). Each entry also names a
`category` (legislative body): "provinciale-staten" (the provinces) or "tweede-kamer". The site is
organized as categories -> scopes; main() writes one data/<key>.json per scope plus a
data/catalog.json index grouping scopes by category. See ../provinces.md and ../data-sources.md.

Zero dependencies (stdlib only) so GitHub Actions needs no install step.
See ../data-sources.md for the reverse-engineered GO endpoints.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, date, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --- Source registry ----------------------------------------------------------
# Each entry: key, name, vendor, category, base, term_start (y,m,d), term_label, style, license.
# `category` defaults to "provinciale-staten"; the Tweede Kamer entry sets "tweede-kamer".
# Add a source here once its vendor adapter exists (see ../provinces.md + ../data-sources.md).
SOURCES = [
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
        # One or more iBabs reports (GET /Reports lists them). These registers track *adopted*
        # items only; verworpen moties/amendementen aren't published here in structured form.
        "reports": [
            {"guid": "84a8ac43-1424-48a9-8a1a-0c0bbcdfd8ed", "type": "motie"},
            {"guid": "95a2053b-5dd6-4aa4-9e60-fdf5158fc48f", "type": "amendement"},
        ],
        "term_start": (2023, 3, 29),   # PS election 15 March 2023
        "term_label": "2023-2027",
        "style": {"accent": "#2891e0", "headerBg": "#0e2438"},   # NH portal huisstijl blue
        "license": "Open data - Provincie Noord-Holland (iBabs publieksportaal)",
        # iBabs scope: these registers list adopted items only, and votes are recorded per
        # fractie (not per member), so "ruwe getallen" show 1–0 rather than seat counts.
        "note": "De bron (iBabs-registers) bevat alleen aangenomen moties en amendementen; "
                "stemmen zijn op fractieniveau geregistreerd, dus zonder exacte aantallen per fractie.",
    },
    {
        "key": "limburg",
        "name": "Limburg",
        "vendor": "ibabs",
        "votes": "stemmen",   # structured per-fractie member counts (not NH's free text)
        "base": "https://limburg.bestuurlijkeinformatie.nl",
        "reports": [
            {"guid": "0493fdd4-4d92-45b7-9645-64a5cb38e1dd", "type": "motie"},
            {"guid": "34a4e0ce-064b-4457-9acb-8e89a2a93019", "type": "amendement"},
        ],
        "term_start": (2023, 3, 29),
        "term_label": "2023-2027",
        "style": {"accent": "#0059a2", "headerBg": "#0a2540"},   # Limburg portal huisstijl blue
        "license": "Open data - Provincie Limburg (iBabs publieksportaal)",
        # Richer than NH: includes verworpen moties/amendementen and exact per-fractie counts. Moties
        # zonder hoofdelijke stemming (bij acclamatie) hebben geen telling en worden overgeslagen.
        "note": "Stemmen zijn per fractie met aantallen geregistreerd (aangenomen én verworpen). "
                "Moties/amendementen zonder hoofdelijke stemming zijn niet opgenomen.",
    },
    {
        # A second *category* (not a province): the national parliament. Clean OData v4 API with
        # per-fractie votes incl. seat counts -> tier A. See data-sources.md §8.
        "key": "tweede-kamer",
        "name": "Tweede Kamer",
        "vendor": "tk",
        "category": "tweede-kamer",
        "body": "Tweede Kamer",
        "base": "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0",
        "public": "https://www.tweedekamer.nl",   # human-facing site (per-item: /zoeken?qry={nummer})
        # Current term = Kamer installed after the 29 Oct 2025 election (constituerende verg. 12 Nov;
        # first stemming 13 Nov). Date-gating here drops old-composition votes cast before installation.
        "term_start": (2025, 11, 13),
        "term_label": "2025-heden",
        "style": {"accent": "#154273", "headerBg": "#0c1d33"},   # Rijkshuisstijl blue
        "license": "Open data - Tweede Kamer der Staten-Generaal (opendata.tweedekamer.nl)",
        "compact": True,   # ~3k stemmingen -> write minified JSON to keep the file ~3 MB
        "note": "Stemmen zijn per fractie met zetelaantallen geregistreerd (aangenomen én verworpen). "
                "Alleen stemmingen met een hoofdelijke of fractiegewijze telling; zaken die zonder "
                "stemming zijn afgedaan, aangehouden of ingetrokken zijn niet opgenomen.",
    },
]

# Categories (legislative bodies) -> how the frontend labels the "pick category -> pick scope" UX.
# scope_noun is the word for one scope ("provincie"); None when the category is a single body (TK).
CATEGORY_META = {
    "provinciale-staten": {"name": "Provinciale Staten", "scope_noun": "provincie",
                           "blurb": "Stemgedrag in de 12 provinciale staten — kies een provincie."},
    "tweede-kamer": {"name": "Tweede Kamer", "scope_noun": None,
                     "blurb": "Het landelijke parlement — moties, amendementen en wetsvoorstellen."},
}
CATEGORY_ORDER = ["provinciale-staten", "tweede-kamer"]

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


def fetch(url, data=None, ctype=None, tries=3):
    """http() with retries on transient errors. Returns the body, or None on a 4xx/5xx or after
    `tries` failed attempts. A 30s read timeout over hundreds of pages is normal for a weekly
    run, so retry the non-HTTP failures (timeouts, dropped connections) instead of crashing."""
    for attempt in range(tries):
        try:
            return http(url, data=data, ctype=ctype)
        except urllib.error.HTTPError:
            return None   # 4xx/5xx — not worth retrying for our purposes
        except OSError:   # URLError, TimeoutError, dropped connections, …
            if attempt + 1 == tries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def try_json(url):
    """GET + JSON parse; None on any network/HTTP/JSON failure."""
    txt = fetch(url)
    try:
        return json.loads(txt) if txt is not None else None
    except json.JSONDecodeError:
        return None


def try_text(url):
    """GET returning text (HTML), tolerant of network/HTTP errors."""
    return fetch(url)


def post_json(url, body):
    """POST a form body and parse the JSON response; None on failure."""
    txt = fetch(url, data=body, ctype="application/x-www-form-urlencoded")
    try:
        return json.loads(txt) if txt is not None else None
    except json.JSONDecodeError:
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


def ibabs_status_from_bijlage(html):
    """Reports without a Status field (Amendementen) encode the outcome in the attachment
    filename, e.g. "A8-2026 AANGENOMEN Volt PvdD …". Return the matched keyword, or ""."""
    bij = ibabs_field(html, "Bijlage") or ""
    m = re.search(r"\b(AANGENOMEN|VERWORPEN|INGETROKKEN|AANGEHOUDEN|VERVALLEN|VERDAAGD)\b", bij, re.I)
    return m.group(1).capitalize() if m else ""


def ibabs_title(r):
    title = (r.get("title") or "").strip()
    num = (r.get("motienummer") or "").strip()
    if num and num.lower() not in title.lower():
        return f"{num} — {title}" if title else num
    return title


def _list_year(r):
    """Best 4-digit year from a list row's date-ish fields (schema varies per portal)."""
    for k in ("ingediendindatum", "datum", "registrationdate"):
        m = re.search(r"(?:19|20)\d{2}", str(r.get(k, "") or ""))
        if m:
            return int(m.group(0))
    return 0


def ibabs_fetch(p):
    """Common iBabs fetch: for every report, pull the DataTables list + each in-term detail page.
    Returns [(row, date, html, type, id_base)] with row['status'] resolved (list / detail field /
    attachment filename). Each report gets its own id_base since `identity` restarts per report."""
    base = p["base"].rstrip("/")
    reports = p.get("reports") or [{"guid": p["report"], "type": "motie"}]
    term_start = date(*p["term_start"])
    raw, skipped = [], 0
    for ri, rep in enumerate(reports):
        id_base = ri * 10_000_000
        listing = post_json(f"{base}/Reports/GetReportData/{rep['guid']}", "draw=1&start=0&length=2000")
        rows = listing.get("data") if isinstance(listing, dict) else None
        if not rows:
            print(f"  {rep['type']}: report {rep['guid']} unreachable/empty — skipped")
            continue
        # Pre-filter by year to skip pre-term detail pages; the exact term cut is on the item's own
        # date below (a 1-year margin covers items indiened just before the term).
        cand = [r for r in rows if _list_year(r) >= term_start.year - 1]
        kept = 0
        for r in cand:
            html = try_text(f"{base}/Reports/Item/{r['DT_RowId']}")
            time.sleep(SLEEP)
            if not html:
                skipped += 1
                continue
            # Date label varies per portal: NH "Datum PS", Limburg list "datum" / detail "Datum".
            d = ibabs_date(ibabs_field(html, "Datum PS") or r.get("datum")
                           or ibabs_field(html, "Datum") or r.get("ingediendindatum"))
            if not d or d < term_start:
                continue
            if not (r.get("status") or "").strip():
                r["status"] = ibabs_field(html, "Status") or ibabs_status_from_bijlage(html)
            raw.append((r, d, html, rep["type"], id_base))
            kept += 1
        print(f"  {rep['type']}: {len(rows)} rows, {len(cand)} candidates, {kept} in-term")
    if skipped:
        print(f"  WARN: {skipped} detail page(s) failed to fetch")
    return raw


def ibabs_item(base, r, d, rtype, id_base, votes):
    status = (r.get("status") or "").strip()
    return {
        "id": ibabs_id(r) + id_base,
        "date": d.isoformat(),
        "title": ibabs_title(r),
        "type": rtype,
        "result": ibabs_result(status),
        "resultLabel": status or None,
        "source": f"{base}/Reports/Item/{r['DT_RowId']}",
        "votes": votes,
    }


def ibabs_finalize(items, appear, name_by_slug):
    """Shared tail: per-item totals, newest-first sort, party columns ordered by activity."""
    items.sort(key=lambda m: (m["date"], m["title"]), reverse=True)
    for m in items:
        m["totals"] = {"agree": sum(1 for v in m["votes"].values() if v["agree"] > v["disagree"]),
                       "disagree": sum(1 for v in m["votes"].values() if v["disagree"] > v["agree"])}
    order = sorted(appear, key=lambda s: (-appear[s], name_by_slug[s].lower()))
    by_type = {}
    for m in items:
        by_type[m["type"]] = by_type.get(m["type"], 0) + 1
    print(f"  items with votes: {len(items)} {by_type}; fracties: {len(appear)}")
    return {"parties": [{"slug": s, "name": name_by_slug[s]} for s in order], "moties": items}


def collect_ibabs(p):
    """iBabs province. Two vote formats (set per province via "votes"):
    - "stemverhouding" (default, Noord-Holland): free-text, faction-level, "overige fracties" inferred.
    - "stemmen" (Limburg): structured per-fractie member counts — exact, with real split votes."""
    raw = ibabs_fetch(p)
    if not raw:
        return None
    return (ibabs_assemble_stemmen if p.get("votes") == "stemmen"
            else ibabs_assemble_stemverhouding)(p, raw)


def ibabs_assemble_stemverhouding(p, raw):
    """NH free-text "Stemverhouding". Two passes: build the term party universe (+ a first_seen gate
    for mid-term splinters), then resolve each item's "overige fracties" against the fracties that
    already existed on its date."""
    base = p["base"].rstrip("/")
    term_start = date(*p["term_start"])
    parsed = [(r, d, ibabs_parse(ibabs_field(html, "Stemverhouding")), rtype, id_base)
              for (r, d, html, rtype, id_base) in raw]

    universe, first_seen = set(), {}

    def mark(party, d):
        if party and (party not in first_seen or d < first_seen[party]):
            first_seen[party] = d

    for r, d, spec, rtype, id_base in parsed:
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

    items, appear, name_by_slug = [], {}, {}
    for r, d, spec, rtype, id_base in parsed:
        if not spec:
            continue
        present = {q for q in universe if first_seen.get(q, term_start) <= d}
        voor, tegen, split = ibabs_resolve(*spec, present)
        if not voor and not tegen and not split:
            continue
        votes = {}
        # split (= "verdeeld gestemd") -> agree==disagree, rendered as "O" + split dot.
        for party, agree, disagree in ([(x, 1, 0) for x in voor] + [(x, 0, 1) for x in tegen]
                                       + [(x, 1, 1) for x in split]):
            slug = slugify(party)
            name_by_slug[slug] = party
            votes[slug] = {"agree": agree, "disagree": disagree, "abstain": 0}
            appear[slug] = appear.get(slug, 0) + 1
        items.append(ibabs_item(base, r, d, rtype, id_base, votes))
    return ibabs_finalize(items, appear, name_by_slug)


def ibabs_assemble_stemmen(p, raw):
    """Limburg "Stemmen": structured per-fractie member counts for the voor and tegen sides.
    Self-contained (nothing inferred); a fractie on both sides is a real split (agree>0, disagree>0)."""
    base = p["base"].rstrip("/")
    items, appear, name_by_slug = [], {}, {}
    for r, d, html, rtype, id_base in raw:
        votes = ibabs_parse_stemmen(html, name_by_slug)
        if not votes:
            continue
        for slug in votes:
            appear[slug] = appear.get(slug, 0) + 1
        items.append(ibabs_item(base, r, d, rtype, id_base, votes))
    return ibabs_finalize(items, appear, name_by_slug)


# Limburg "Stemmen" markup: <div class="vote-summary-legend-{in-favour|against}"> … <div
# class="text">Fractie (Statenleden) (N), …</div>. A fractie on both sides = a split vote.
def ibabs_parse_stemmen(html, name_by_slug):
    m = re.search(r"<dt[^>]*>\s*Stemmen\s*</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.S)
    if not m:
        return {}
    block = m.group(1)
    votes = {}

    def side(css, key):
        sm = re.search(r'vote-summary-legend-' + css + r'\b.*?<div class="text">(.*?)</div>', block, re.S)
        if not sm:
            return
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sm.group(1))).strip()
        for name, cnt in ibabs_stemmen_items(text):
            slug = slugify(name)
            name_by_slug.setdefault(slug, name)
            votes.setdefault(slug, {"agree": 0, "disagree": 0, "abstain": 0})[key] += cnt

    side("in-favour", "agree")
    side("against", "disagree")
    return votes


def ibabs_stemmen_items(text):
    """"50PLUS (Statenlid) (1), CDA (Statenleden) (4), Horizon (1)" -> [(canon_name, count)].
    Fractie names contain no commas in this summary, so a plain comma split is safe."""
    out = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        m = re.match(r"^(.*?)\s*(?:\((?:Statenlid|Statenleden)\)\s*)?\((\d+)\)\s*$", chunk)
        if m:
            name = ibabs_canon(m.group(1))
            if name:
                out.append((name, int(m.group(2))))
    return out


# --- Tweede Kamer (OData) adapter ---------------------------------------------
# The Tweede Kamer publishes an OData v4 API (gegevensmagazijn.tweedekamer.nl). The vote chain is
# Stemming -> Besluit -> Zaak (the motie/amendement/wetsvoorstel) + Agendapunt -> Activiteit (date).
# $expand inlines the children and nested navigation is filterable, so one paged query (250/page,
# follow @odata.nextLink) pulls everything. Votes are per fractie WITH seat counts (FractieGrootte)
# -> exact tallies, tier A. See data-sources.md §8 for the full reverse-engineering notes.

# Stemming.ActorFractie is the fractie name AT vote time, so a mid-term rename yields two names for
# one group. Merge a pure rename into a single column (GroenLinks-PvdA was renamed "Progressief
# Nederland" on 2026-06-09; most of the term it was GL-PvdA, so keep that as the display name).
TK_ALIASES = {"Progressief Nederland": "GroenLinks-PvdA"}
TK_TYPE = {"Motie": "motie", "Amendement": "amendement", "Wetgeving": "wetsvoorstel"}


def tk_result(besluitsoort):
    """Map BesluitSoort -> (result, label). Check 'niet aangenomen'/'verworpen' before 'aangenomen'
    (the former contains the latter as a substring)."""
    s = (besluitsoort or "").lower()
    if "niet aangenomen" in s or "verworpen" in s:
        return "rejected", "Verworpen"
    if "gestaakt" in s:
        return "tie", "Staken van stemmen"
    if "aangenomen" in s or "goedgekeurd" in s or "vastgesteld" in s:
        return "accepted", "Aangenomen"
    return None, (besluitsoort or None)


def tk_pick_zaak(zaken):
    """A besluit can link to several Zaken; pick the most table-worthy one (motie > amendement >
    wetsvoorstel) and ignore the rest (covering documents, etc.)."""
    ranked = [(("Motie", "Amendement", "Wetgeving").index(z["Soort"]), z)
              for z in zaken if z.get("Soort") in TK_TYPE]
    if not ranked:
        return None
    return min(ranked, key=lambda x: x[0])[1]


def tk_item(public, b, name_by_slug, seats):
    """Build one normalized stemming dict from a Besluit (with expanded Stemming/Zaak/Agendapunt),
    or None if it isn't a usable per-fractie vote on a motie/amendement/wetsvoorstel."""
    z = tk_pick_zaak(b.get("Zaak") or [])
    if not z:
        return None
    rtype = TK_TYPE.get(z.get("Soort"))
    if not rtype:
        return None
    act = (b.get("Agendapunt") or {}).get("Activiteit") or {}
    dt = (act.get("Datum") or "")[:10]
    if not re.match(r"\d{4}-\d{2}-\d{2}$", dt):
        return None
    votes = {}
    for s in b.get("Stemming") or []:
        fr = TK_ALIASES.get((s.get("ActorFractie") or s.get("ActorNaam") or "").strip(), None) \
             or (s.get("ActorFractie") or s.get("ActorNaam") or "").strip()
        if not fr:
            continue
        slug = slugify(fr)
        name_by_slug.setdefault(slug, fr)
        g = s.get("FractieGrootte") or 0
        seats[slug] = max(seats.get(slug, 0), g)
        v = votes.setdefault(slug, {"agree": 0, "disagree": 0, "abstain": 0})
        soort = s.get("Soort")
        if soort == "Voor":
            v["agree"] += g
        elif soort == "Tegen":
            v["disagree"] += g
        else:                       # "Niet deelgenomen" / null
            v["abstain"] += g
    if not any(v["agree"] or v["disagree"] for v in votes.values()):
        return None   # roll-call with no actual voor/tegen (shouldn't happen, but guard)
    result, label = tk_result(b.get("BesluitSoort"))
    nummer = (z.get("Nummer") or "").strip()
    title = (z.get("Onderwerp") or z.get("Titel") or "").strip()
    return {
        "id": int(b["Id"].replace("-", "")[:12], 16),   # GUID -> stable int (frontend coerces +id)
        "date": dt,
        "title": title,
        "type": rtype,
        "result": result,
        "resultLabel": label,
        "source": (public.rstrip("/") + "/zoeken?qry=" + urllib.parse.quote(nummer)) if nummer else public,
        "votes": votes,
    }


def collect_tk(p):
    """Tweede Kamer. One paged OData query (with $expand) pulls every in-term roll-call besluit on a
    motie/amendement/wetsvoorstel, votes inlined. Self-contained per besluit (exact seat counts)."""
    base = p["base"].rstrip("/")
    public = p.get("public", base)
    term_start = date(*p["term_start"])
    term_iso = term_start.isoformat() + "T00:00:00Z"
    filt = ("startswith(BesluitSoort,'Stemmen') "
            "and Agendapunt/Activiteit/Datum ge " + term_iso + " "
            "and Stemming/any() "
            "and Zaak/any(z: z/Soort eq 'Motie' or z/Soort eq 'Amendement' or z/Soort eq 'Wetgeving')")
    expand = ("Stemming($select=ActorFractie,ActorNaam,Soort,FractieGrootte),"
              "Zaak($select=Nummer,Soort,Onderwerp,Titel),"
              "Agendapunt($expand=Activiteit($select=Datum))")
    qs = urllib.parse.urlencode(
        {"$filter": filt, "$expand": expand, "$select": "Id,BesluitSoort,BesluitTekst",
         "$orderby": "GewijzigdOp desc", "$format": "json"},
        quote_via=urllib.parse.quote)
    url = base + "/Besluit?" + qs

    items, appear, name_by_slug, seats, seen = [], {}, {}, {}, set()
    pages = 0
    while url:
        data = try_json(url)
        if not data:
            break
        for b in data.get("value", []):
            it = tk_item(public, b, name_by_slug, seats)
            if not it or it["id"] in seen:
                continue
            seen.add(it["id"])
            items.append(it)
            for slug in it["votes"]:
                appear[slug] = appear.get(slug, 0) + 1
        pages += 1
        url = data.get("@odata.nextLink")
        time.sleep(SLEEP)
    print(f"  fetched {pages} page(s); {len(items)} stemmingen; {len(appear)} fracties")
    if not items:
        return None

    items.sort(key=lambda m: (m["date"], m["title"]), reverse=True)
    for m in items:
        m["totals"] = {"agree": sum(v["agree"] for v in m["votes"].values()),
                       "disagree": sum(v["disagree"] for v in m["votes"].values())}
    # Columns ordered by current fractie size (biggest first), then activity, then name.
    order = sorted(appear, key=lambda s: (-seats.get(s, 0), -appear[s], name_by_slug[s].lower()))
    by_type = {}
    for m in items:
        by_type[m["type"]] = by_type.get(m["type"], 0) + 1
    print(f"  types: {by_type}")
    return {"parties": [{"slug": s, "name": name_by_slug[s]} for s in order], "moties": items}


def province_granularity(p):
    """Vote detail level, for the frontend: "member" = real per-fractie counts (GO, Limburg
    "stemmen") so "ruwe getallen" are meaningful; "fractie" = faction-level V/T only
    (NH "stemverhouding"), where counts are just 1/0 and must not be shown as tallies."""
    if p["vendor"] == "ibabs" and p.get("votes", "stemverhouding") == "stemverhouding":
        return "fractie"
    return "member"


ADAPTERS = {"go": collect_go, "ibabs": collect_ibabs, "tk": collect_tk}


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    scopes_by_cat = {}   # category key -> list of {key, name, available}
    default = None
    for p in SOURCES:
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
                    "body": p.get("body", "Provinciale Staten"),
                    "term": p["term_label"],
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "source": p.get("public", p["base"]),
                    "license": p.get("license", ""),
                    "style": p.get("style", {}),
                    "note": p.get("note", ""),
                    "granularity": province_granularity(p),
                    "counts": {"moties": len(res["moties"]), "parties": len(res["parties"])},
                },
                "parties": res["parties"],
                "moties": res["moties"],
            }
            # Large datasets (TK) write minified to keep the static file small.
            dump = (json.dumps(out, ensure_ascii=False, separators=(",", ":")) if p.get("compact")
                    else json.dumps(out, ensure_ascii=False, indent=2))
            (DATA_DIR / f"{p['key']}.json").write_text(dump, encoding="utf-8")
            by_type = {}
            for m in res["moties"]:
                by_type[m["type"]] = by_type.get(m["type"], 0) + 1
            print(f"  wrote {p['key']}.json: {len(res['moties'])} stemmingen, "
                  f"{len(res['parties'])} fracties, {by_type}")
        else:
            print("  (no data — marked unavailable)")
        catkey = p.get("category", "provinciale-staten")
        scopes_by_cat.setdefault(catkey, []).append(
            {"key": p["key"], "name": p["name"], "available": available})
        if available and default is None:
            default = {"category": catkey, "scope": p["key"]}

    # catalog.json — the frontend's "pick category -> pick scope" index.
    categories = []
    for catkey in CATEGORY_ORDER:
        scopes = scopes_by_cat.get(catkey)
        if not scopes:
            continue
        meta = CATEGORY_META[catkey]
        categories.append({"key": catkey, "name": meta["name"], "scopeNoun": meta["scope_noun"],
                           "blurb": meta["blurb"], "scopes": scopes})
    (DATA_DIR / "catalog.json").write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "default": default, "categories": categories},
        ensure_ascii=False, indent=2), encoding="utf-8")
    avail = [s["key"] for c in categories for s in c["scopes"] if s["available"]]
    print(f"\nWrote catalog.json: categories = {[c['key'] for c in categories]}; available = {avail}")


if __name__ == "__main__":
    sys.exit(main())
