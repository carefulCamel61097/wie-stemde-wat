# Roadmap — "Wie heeft wat gestemd?" (multi-province voting overview)

> ## ▶ NEXT (resume here)
> **TARGET — LOCKED (2026-06-12): four categories.** The site's scope is now four legislative bodies
> (landing order: national → regional → EU):
> 1. **Tweede Kamer** — ✅ LIVE (Phase 4). ~2,974 stemmingen, OData, per-fractie seat counts incl. verworpen.
> 2. **Eerste Kamer** — ⏳ NEXT. Phase 5 below. **Do a feasibility probe FIRST** (own system, separate
>    from the TK API; much voting is *bij zitten en opstaan* / zonder stemming → likely faction-level
>    tier B, possibly no breakdown on some votes). Confirm data before building.
> 3. **Provinciale Staten** — ◑ category LIVE, 3/12 provinces (Utrecht, Noord-Holland, Limburg).
>    Growing it to more provinces is the outreach track below (Notubiz token + griffie lobby).
> 4. **Europees Parlement** — ⏳ NEXT. Phase 6 below. **Feasibility probe FIRST.** EP publishes
>    **roll-call votes for ALL MEPs** (open data) → present by **European political group** (not only
>    Dutch MEPs), Dutch delegation optional. Confirm source + model before building.
>
> The architecture is ready: catalog (categories→scopes) + frontend landing/routing already support new
> categories, so EK/EP = "feasibility probe → new adapter → catalog entry" (no IA refactor). Each new
> category is single-scope (like TK), so it opens straight to its table.
>
> **In parallel — Provinciale Staten growth (blocked on replies, both SENT, awaiting):**
> - **Notubiz token** ([outreach.md](outreach.md) §1, sent 2026-06-10) → up to 5 provinces (Fryslân,
>   Groningen, Zuid-Holland, Overijssel; Gelderland outcome-only). `api.notubiz.nl/agenda_items/votings`
>   + token unlocks the `role_id → fractie` map (`/roles?field_id=105`).
> - **Griffie mails** ([outreach.md](outreach.md) §2, sent 2026-06-12 to `griffie@flevoland.nl` +
>   `Statengriffie@drentsparlement.nl`) → if they enable the GO stemgedrag module, Flevoland/Drenthe
>   become config-only. (PDF-parsing rejected: fragile, per-griffie, low ROI.)
>
> **Parked categories (decided NOT to pursue):** gemeenteraden (~340 — fragmented, local, not national
> news, low per-unit salience) and waterschappen (elected but niche/low-profile). Reconsider only on demand.
>
> Frontend shipped beyond v1: category→scope landing + hash routing (deep-linkable/shareable), CSV export
> (atomic columns), matrix min-vote filter + greyed low-n cells, per-scope `granularity`, delegated pins.

> **DONE (Phase 3d):** iBabs adapter (`collect_ibabs`) built; **Noord-Holland** (181 items, faction-
> level, aangenomen only) and **Limburg** (321 items, **per-member counts incl. verworpen**) live as
> provinces 2 & 3. Adapter unions multiple reports per province and supports two vote formats
> (`votes`: `stemverhouding` = NH free-text, `stemmen` = Limburg structured counts). The other two
> iBabs provinces are **dead ends**: **Zeeland** registers are empty; **Noord-Brabant** publishes
> outcomes but no per-fractie breakdown. Coverage + per-source **reliability**: [coverage.md](coverage.md).

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
- **Province selector** — built from `data/provinces.json` (live: Utrecht, Noord-Holland, Limburg).
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
- Shareable URL encoding filter state. Member-level detail (privacy: later).
- ✅ CSV download (filtered rows → semicolon CSV + BOM) — DONE.
- Other bodies (Tweede Kamer, etc.).

### Multi-province (Phase 3) — discovery done, see [provinces.md](provinces.md)
3a complete. Key finding: the clean per-party vote API is **Utrecht-only** (GO stemgedrag
module is opt-in; Flevoland/Drenthe GO have the API but votes 404). Vendor split: GO 3,
Notubiz 5, iBabs 4. iBabs + Notubiz are JS SPAs → votes need backend reverse-engineering
(one effort per vendor unlocks its 4–5 provinces); they expose **faction-level** votes
(fine for V/T, degrades "ruwe getallen"/split).
- **3b DONE**: collector has a PROVINCES registry + pluggable vendor adapters; frontend is
  province-driven (selector from `data/provinces.json`, per-province data + huisstijl).
- **3c DONE**: cracked the iBabs vote endpoints (data-sources.md §7).
- **3d DONE**: built the iBabs adapter (`collect_ibabs`) and shipped **Noord-Holland** (2nd
  province). Votes are faction-level (`agree/disagree = 1/0`); NH's motieregister holds
  *aangenomen* moties only (surfaced via `meta.note`).
- **Next**: replicate to the other iBabs provinces (Limburg, Noord-Brabant, Zeeland) — see the
  NEXT block at the top — and/or crack **Notubiz** (5 provinces) once a token arrives.
- **Action — lobby for the easy wins**: e-mail the Statengriffie of **Flevoland** and **Drenthe**
  (GO provinces) asking them to enable the GO **stemgedrag** module / publish per-party votes as
  open data like Utrecht. If they do, those provinces become config-only (free). Same ask could
  apply to Notubiz provinces with the module off (e.g. Gelderland). Contact the province, not GO.

### Phase 4 — Tweede Kamer + category split  ✅ DONE (2026-06-11)
The first **second category** (legislative body) beyond Provinciale Staten. Realizes the
"pick **category** → pick **scope** → see the table" UX from [context.md](context.md). TK is not a
province, so the frontend's province-only model was generalized into a category→scope **catalog**.
**Shipped:** `collect_tk` adapter → `data/tweede-kamer.json` (~2,945 stemmingen, minified ~3 MB);
`main()` now writes `data/catalog.json` (categories→scopes, replacing `provinces.json`); the
frontend has a home/landing view, a category→scope picker, and URL-hash routing. The 4a/4b/4c notes
below are the as-built record.

**Why TK over the remaining provinces:** clean documented open-data API *with* per-fractie votes
(no scraping), national audience, same normalized schema. Beats PDF-parsing 2 GO provinces and isn't
blocked like Notubiz.

**4a — Probe the API (do FIRST, before any code).**
- Source: **`https://opendata.tweedekamer.nl`** — the official OData v4 / SyncFeed API (no auth, no
  formal token). Vote chain to verify: `Besluit` → `Stemming` (per-fractie) → `Fractie`
  (`ActorFractie` + `FractieZetelAantal` for seat counts), linked to `Zaak`/`Document` (motie /
  amendement / wetsvoorstel) and the `Activiteit`/`Vergadering` for the date.
- Confirm: per-fractie **seat counts** are present (→ granularity `member`, tier A like Utrecht),
  how to scope to the **current term** (post-2025 election), item-type classification, and the
  outcome field (aangenomen/verworpen).
- **Measure data size.** TK volume ≫ a province. The page loads one whole JSON; if `tweede-kamer.json`
  is multi-MB, term-scope hard and/or trim fields (and only then consider per-year splits). Decide
  after measuring — don't pre-optimize.

**4b — IA refactor (independent of the API; can land first).**
- **Catalog data model:** generalize `data/provinces.json` into a catalog of **categories →
  scopes**. Each category = a body (`tweede-kamer`, `provinciale-staten`); each scope flags
  `available` + its data file. TK is a category with a **single** scope.
- **Home view (NOT a separate page):** one `index.html`, with a landing/home *view state* shown when
  no scope is selected. The table + all popups (matrix, partijprofiel, vergelijken) are byte-for-byte
  shared between TK and PS — do **not** fork into two pages.
- **Two-level selector:** category → scope. Scope picker only appears for categories with >1 scope;
  a single-scope category (TK) goes **straight to the table** (no dead-end second click). Moving
  scope selection up to the home view declutters the table header.
- **Hash routing:** selection lives in the URL (`#tk`, `#ps/utrecht`). Delivers three things at once:
  the declutter, **shareable/deep-linkable URLs** (the parked v1.1 feature — now delivered here), and
  **SEO** (distinct URLs per body/scope, compounding the meta/OG work already shipped).

**4c — TK adapter.**
- New adapter (e.g. `collect_tk`) in `collector/collect.py`, writing `data/tweede-kamer.json` in the
  **same normalized schema** (parties = fracties, votes per fractie with seat counts). Register TK in
  the catalog and add it to the weekly GitHub Actions cron.

### Phase 5 — Eerste Kamer (PLANNED — feasibility probe FIRST)
The revising chamber (Senate, 75 seats, indirectly elected by the Provinciale Staten). Completes the
national parliament (Staten-Generaal). A single-scope category like TK.

**5a — Feasibility probe (do before any code; gate the whole phase on it).**
- **Source unknown/to confirm:** the Eerste Kamer is a *separate* system from the TK OData
  (`gegevensmagazijn.tweedekamer.nl` is TK-only). Candidates to check: an EK open-data API on
  `eerstekamer.nl`, the joint `officielebekendmakingen.nl`/SGD, or an EK gegevensmagazijn. Find where
  per-stemming, per-fractie data lives (if anywhere).
- **Expect tier B or thinner.** The EK votes a lot **bij zitten en opstaan** or **zonder stemming**
  (chair declares the result, only the *tegen* fracties noted — no counts); exact per-member numbers
  only on a requested **hoofdelijke stemming**. So realistic best case = faction-level V/T (like NH),
  and some votes may have **no per-fractie breakdown at all**. Decide go/no-go from what the probe finds.
- If viable: `collect_ek` adapter → `data/eerste-kamer.json`, category `eerste-kamer`, single scope.
  Set `granularity` honestly (likely "fractie"). Document the caveats in [coverage.md](coverage.md).

### Phase 6 — Europees Parlement (PLANNED — feasibility probe FIRST)
The EU's elected chamber (the EU's democratic-vote layer; the Council = governments, not in scope).
Single-scope category. **Present votes by European political group** (EPP, S&D, Renew, Greens/EFA,
ECR, The Left, PfE, ESN, NI), with the Dutch delegation as an optional breakout — **not Dutch MEPs only**.

**6a — Feasibility probe (first).**
- **Sources to check:** the EP Open Data Portal (`data.europarl.europa.eu`, has roll-call vote / RCV
  data) and/or the well-known `HowTheyVote.eu` datasets. Confirm: per-MEP RCV results, mapping MEP →
  political group (and → national party for the NL breakout), titles/dates, and outcome.
- **Caveats to confirm:** only **roll-call** votes are recorded per-MEP (show-of-hands aren't); volume
  is large (scope to the current term, write compact like TK); the unit is **political group**, so the
  schema's "parties" = groups (new ABBR/colour set). Member-level → aggregate to group (privacy: RCVs
  are public record, same as TK).
- If viable: `collect_ep` adapter → `data/europees-parlement.json`, category `europees-parlement`.

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
- Refresh: **GitHub Actions weekly cron** (Thu 06:00 UTC — day after the usual Wed
  Statenvergadering) + manual dispatch. Live & verified in `.github/workflows/refresh.yml`.
- Privacy: v1 party-level only (no member names). Member-level = personal data, later.
- **Domain**: SETTLED — free `*.github.io`, no custom domain (can revisit later, not planned).
- **Transpose view**: SETTLED — will NOT add; deselecting all-but-one party already gives a
  single-party view, so it's unnecessary (see dropped note above).
- **Category scope**: LOCKED (2026-06-12) to **four** bodies — Tweede Kamer, Eerste Kamer,
  Provinciale Staten, Europees Parlement. Gemeenteraden + waterschappen explicitly **parked** (see
  the NEXT block). EK + EP are each gated on a feasibility probe (Phases 5–6).

## Cost
€0 with GitHub (repo + Pages + Actions) and a free `*.github.io` domain. Only a custom
domain costs money (optional, later).

## Future categories (same architecture)
Target set (LOCKED, 2026-06-12): **Tweede Kamer** ✅, **Eerste Kamer** (Phase 5), **Provinciale
Staten** ◑, **Europees Parlement** (Phase 6). Each = a new adapter feeding the same frontend (a new
category/scope in the catalog; the IA already supports it). **Parked** (not pursuing now): gemeenteraden
(fragmented/local/low-profile) and waterschappen (niche). The Council of the EU is out of scope (it's
governments negotiating, not an elected chamber).
