# Moties — "Wie heeft wat gestemd?" voting-overview project

## Vision
A website that answers **"Ik wil zien wie wat gestemd heeft in …"**.

- Landing page: a headline "Ik wil zien wie wat gestemd heeft in de provinciale staten",
  then the user **picks a province**, then sees a table of how each party voted on each
  motie in that province.
- Later: more categories ("… in de Tweede Kamer", gemeenteraden, etc.). So the UX is:
  pick a **category** (which legislative body) → pick the **scope** (e.g. province) →
  see the table. Other plausible categories: Tweede Kamer, Eerste Kamer, gemeenteraden,
  Europees Parlement, waterschappen — each is "an adapter → same frontend".

## What the table shows
Rows = moties, columns = parties (fracties). Each cell: **V** (green, *Voor*) or
**T** (red, *Tegen*), with **-** (grey) for a tie, and blank/grey for *afwezig*.

Cell value rule: per party per motie we have two numbers (voor, tegen) — usually the
whole fractie votes the same. V/T = `voor > tegen`. We keep BOTH numbers stored so the
rare split votes / abstentions / absences stay visible (tooltip, and useful later).

## Views (built — all from one dataset)
1. Main table: moties as rows, parties as columns. Filters (type chips, party show/hide,
   search, result, "alleen omstreden"), pin rows, sort, raw-numbers toggle, legend/help popups.
2. **Overeenkomst** popup — party-agreement matrix (clustered so like-voting parties sit together).
3. **Partijprofiel** popup — % aan de winnende kant, totals, lone-dissenter list.
4. **Vergelijken** popup — two parties → the stemmingen where they voted differently.
(Transpose / moties-as-columns was considered and DROPPED — titles too long; a single-party
view is already possible by deselecting parties.)

## Key facts established
- Provincial voting data exists and is **open data** — see [data-sources.md](data-sources.md).
- BUT provinces run **different platforms** (GemeenteOplossingen / iBabs / Notubiz), so
  there is no single endpoint — we need **one adapter per vendor**. Utrecht = GO.
- A nationally unified source (OpenBesluitvorming) exists but covers only 6 provinces and
  has weak *vote* coverage → not our primary source.
- We do need our own **generated dataset** (static JSON), not because of a live DB, but to
  (a) union all moties, (b) normalize across vendors, (c) avoid CORS / live hammering.
- Voting is recorded **per individual member**; v1 stays at **party level** (no names →
  no personal-data concerns).

## v1 scope decisions (locked / pending)
- [x] **Period**: current term only (2023–2027).
- [x] **Stack**: Python (collector).
- [x] **Provinces**: v1 shipped **Utrecht only** with a multi-province-ready UI; **now live with
  Utrecht, Noord-Holland and Limburg** (v2 — province selector active).
- [x] **What to include**: moties + amendementen + besluiten + ordevoorstellen, with a type filter.
- [x] **Body**: Provinciale Staten plenair only (not commissies — those don't hold the votes).
- [x] **Categories (LOCKED 2026-06-12)**: four legislative bodies — **Tweede Kamer** (live),
  **Eerste Kamer** (live, Phase 5), **Provinciale Staten** (live, 3/12 provinces), **Europees
  Parlement** (live, Phase 6). **All four target categories now live.** Gemeenteraden + waterschappen
  parked. See [roadmap.md](roadmap.md).

## Status (June 2026)
- [x] **v1 LIVE** — Utrecht: collector (GO adapter) → `data/utrecht.json` → static site, themed
  to the provincie huisstijl. Weekly GitHub Actions refresh (Thu, day after the Wed vergadering),
  verified. Three analysis popups + help/legend. Hosted on GitHub Pages.
- [x] **Phase 3a** — mapped all 12 provinces to vendor + vote feasibility ([provinces.md](provinces.md)).
- [x] **Phase 3b** — collector + frontend generalized to multi-province (PROVINCES registry +
  vendor adapters, `data/provinces.json` index, province selector, per-province theme).
- [x] **Phase 3c** — cracked the iBabs vote endpoints ([data-sources.md](data-sources.md) §7).
- [x] **Phase 3d** — built the iBabs adapter (`collect_ibabs`, two vote formats) and shipped
  **Noord-Holland** (181 items, faction-level, aangenomen only) and **Limburg** (321 items,
  per-member counts **incl. verworpen**) as provinces 2 & 3. Zeeland (empty) and Noord-Brabant
  (no per-fractie breakdown) are dead ends. Coverage + reliability: [coverage.md](coverage.md).
- [x] **Phase 4** — added the **Tweede Kamer** as a second *category* (not a province): clean OData
  API, per-fractie seat counts incl. verworpen, ~2,945 stemmingen (moties/amendementen/wetsvoorstellen,
  term 2025–heden). Generalized the frontend to **categories → scopes**: a landing page (pick niveau →
  scope), `data/catalog.json` index, and URL-hash routing (`#tweede-kamer`, `#provinciale-staten/utrecht`)
  → deep-linkable + decluttered table header. The "pick category → scope" vision is now real.
- [x] **Phase 5** — added the **Eerste Kamer** (`collect_ek` → `data/eerste-kamer.json`): no machine
  API, so the per-fractie voor/tegen lists are parsed from the HTML "stemmingen per vergaderdag" pages
  (449 stemmingen, term 2023–2027). Faction-level V/T, both sides named (nothing inferred), tier B;
  hoofdelijke (per-member) votes aggregated to the fractie. Third category live.
- [x] **Phase 6** — added the **Europees Parlement** (`collect_ep` → `data/europees-parlement.json`):
  HowTheyVote.eu JSON API (`stats.by_group`) → **exact per-group MEP counts**, presented by European
  political group (545 votes, term 2024–2029, tier A). Concurrent detail fetch (the API is ~1.5s/call).
  **Fourth and final target category live** — the locked 4-category target is complete. Plus a **second
  EP view** ("Nederlandse afvaardiging"): the 31 NL MEPs by national party, with MEP rosters (NL→party
  map from the EP Open Data Portal). Source attribution credits HowTheyVote.eu (ODbL).
- [ ] **NEXT** — grow Provinciale Staten: Notubiz (5 provinces, needs a token — see
  [outreach.md](outreach.md)); GO
  Flevoland/Drenthe via the griffie lobby. See the **NEXT** pointer at the top of [roadmap.md](roadmap.md).

Repo: https://github.com/carefulCamel61097/wie-stemde-wat ·
Live: https://carefulcamel61097.github.io/wie-stemde-wat/
