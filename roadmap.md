# Roadmap — "Wie heeft wat gestemd?" (multi-province voting overview)

v1 goal: a website where you pick a **province** and see a table — rows = moties,
columns = parties, cells = **V** (green) / **T** (red) / **-** (tie) / blank (afwezig).
Free to build and host. See [context.md](context.md) and [data-sources.md](data-sources.md).

## Architecture (static, free, vendor-agnostic)
No live DB/server. A build-time collector produces normalized static JSON per province;
the site just reads it.

```
 per-vendor adapters                normalized                static site (HTML+JS)
 ┌─ GO     (Utrecht, Flevoland) ─┐   dataset
 ├─ iBabs  (Noord-Holland, …)   ─┼─▶ data/<province>.json ─▶  table views  ─▶ GitHub Pages
 └─ Notubiz(Overijssel, …)      ─┘   (the "union" step)            ▲
        ▲                                                          │
        └──────  GitHub Actions cron (weekly) re-runs + commits ───┘
```

Why a generated dataset (our "database") is needed even though V/T is just for>against:
1. **Union** of all moties across parties must be computed somewhere (a party absent for a
   motie is omitted from its own list).
2. **Normalization** across GO / iBabs / Notubiz (different JSON shapes).
3. **CORS / politeness / speed** — the browser can't/shouldn't call 12 provincial sites live.

Notes on "no server":
- Hosting serves only files (no server-side compute).
- The dataset is a **data file** (`data/<province>.json`), not a navigable page; it has a
  URL but users never visit it — the table page fetches it via JS.
- The JSON stores **raw counts** (`{agree,disagree,abstain}` per party); V/T is derived in
  the browser. Never store only V/T.
- The collector runs **manually (v1)** or via a free **GitHub Actions cron** that commits
  refreshed JSON — no server we manage.
- v1 reality: **Utrecht only**, but the UI ships with a province selector (only Utrecht
  selectable) so multi-province (v2) drops in without a redesign.

Common normalized schema (draft):
```
province, term, motie_id, date, type (motie|amendement|besluit|...), title, result,
votes: { "<party>": { agree, disagree, abstain } }   # absent party => key missing
```

## Steps

### Phase 0 — Finish scoping
- Map all 12 provinces → vendor + endpoint (table started in data-sources.md §6).
- Lock v1 scope (provinces included, item types included).

### Phase 1 — GO adapter + collector  ✅ DONE (`collector/collect.py`)
1. ✅ Party list from `/api/v2/groups` (type Fractie) + slugify (page mixes people).
2. ✅ Per party: `GET /Samenstelling/{slug}/votings` → per-party counts.
3. ✅ **Union** by `votingId`; cell = counts (missing ⇒ afwezig).
4. ✅ Date via `meetingId → /api/v2/meetings/{id}` (cached); filter to term ≥ 2023-03-29.
5. ✅ Classify type (motie / amendement / besluit / ordevoorstel; handles word + code form).
6. ✅ Writes `data/utrecht.json`. Polite (0.3s delay). Stdlib only.
   → First run: **566 stemmingen, 16 partijen** (motie 320, amendement 179, besluit 65,
     ordevoorstel 2), bereik 2023-05-31 .. 2026-06-03.

### Phase 2 — Frontend  ✅ DONE (`index.html` at repo root)
Served from repo root (GitHub Pages "deploy from branch" only allows root or /docs), loads
`data/utrecht.json`. Implements the locked v1 feature set: province selector, type chips,
party show/hide, search, pin + show-only-pinned, sort, result filter, "alleen omstreden",
raw-numbers toggle, split-vote markers, legend, source links, sticky header + first column.
Vanilla JS/CSS, no dependencies. `.nojekyll` added. Transpose/party-compare view = parked v1.1.

### Phase 3 — More vendors + publish + automate
10. Add iBabs and Notubiz adapters → more provinces, same schema.
11. GitHub Pages hosting; GitHub Actions weekly cron to refresh + commit data.

## v1 UI — feature set (LOCKED selection)
In v1 (curated from the brainstorm):
- **Province selector** — only Utrecht selectable (multi-province-ready shell).
- **Type filter** — multi-select **chips** (motie / amendement / besluit / ordevoorstel),
  all on by default.
- **Parties** — checklist dropdown to show/hide columns (16 parties).
- **Text search** on title/indiener.
- **Pin** rows → pinned table at top + "toon alleen vastgepind" toggle.
  (Pin, not star. A full motie dropdown would be far too long.)
- **Sort** (date ↑/↓, result) + **filter by result** (aangenomen/verworpen).
- **"Alleen omstreden"** toggle — only stemmingen where parties disagreed.
- **Tooltips** with raw counts + a **raw-numbers toggle** (V/T ↔ "6–0").
- **Legend**, color-blind safe (letter + color), **link to source** per stemming.
- **Highlight split votes** (a fractie not unanimous).
- Party columns ordered by the site's `sortOrder` (already in the data).
- Responsive + sticky first row/column.

Cell display (LOCKED):
- **V** green = `agree > disagree` (voor)
- **T** red  = `disagree > agree` (tegen)
- **O** grey = tie or abstain-majority (onthouden)
- **blank** light-grey = afwezig (party absent for that stemming → not in its data)
- small marker (•) on V/T when the fractie was **not unanimous** (split vote)

Extra views (data already supports these):
- ✅ **Party-agreement matrix** (popup) — parties × parties heatmap, % of stemmingen where
  each pair voted the same. DONE.
- ❌ **Transpose view (moties as columns)** — DROPPED: motie titles are too long to be
  column headers; a single-party view is already possible by deselecting all but one party.
- ✅ **Party profile** (popup) — % on the winning side, voor/tegen/onthouden/afwezig totals,
  and the lone-dissenter list. Party picker + type chips. DONE.
- ✅ **Compare two parties** (popup) — % agreement + list of stemmingen where they differ,
  with V/T/O badges. Two pickers + type chips. DONE.
- ⏳ (optional) link matrix cell click → open Compare for that pair, pre-filled.

Parked (v1.1 / v2):
- Shareable URL encoding filter state. CSV download. Member-level detail (privacy: later).
- Multi-province (iBabs + Notubiz adapters). Other bodies (Tweede Kamer, etc.).

## Decisions
**Locked**
- Period: current term (2023–2027) only.
- Stack: Python (collector). Frontend: dependency-light HTML/JS.
- Body: Provinciale Staten plenair only (commissies don't hold the votes).
- Source strategy: per-vendor adapters; OpenBesluitvorming only as cross-check/fallback.
- Provinces in v1: **Utrecht only**, UI multi-province-ready (selector offers only Utrecht).
- No server: static hosting + JSON data file (raw counts) + manual/Actions-cron collector.
- Item types: include moties + amendementen + besluiten, with the type multi-select filter.

- Item types: include moties + amendementen + besluiten + ordevoorstellen, type filter (chips).
- Cell display + edge cases: locked (see "v1 UI" above).
- Refresh: **GitHub Actions weekly cron** (Mon 06:00 UTC) + manual dispatch. Scaffolded in
  `.github/workflows/refresh.yml`.
- Privacy: v1 party-level only (no member names). Member-level = personal data, later.

**Open**
- **Domain**: free `*.github.io` (v1) vs custom domain later (small cost).
- **Transpose view**: in v1 or as the first v1.1 fast-follow? (currently parked → v1.1)

## Cost
€0 with GitHub (repo + Pages + Actions) and a free `*.github.io` domain. Only a custom
domain costs money (optional, later).

## Future categories (same architecture)
Tweede Kamer (own open-data API w/ votes), Eerste Kamer, gemeenteraden, Europees
Parlement, waterschappen — each = a new adapter feeding the same frontend.
