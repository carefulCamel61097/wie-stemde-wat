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

## Planned views (frontend, all from one dataset)
1. Moties as rows, parties as columns (default).
2. Pick a party (or a selection of parties to compare) → parties as rows, moties as cols.
3. In view 1, be able to **deselect moties** to shrink the list and compare more easily.
Plus filters (by type, date, party).

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
- [x] **Provinces in v1**: **Utrecht only**. But build the UI multi-province-ready: there
  IS a province selector, it just only offers Utrecht for now (multi-province = v2).
- [ ] **What to include**: moties only, or also amendementen / besluiten (with filters)?
  (leaning: include all, filter by type)
- [x] **Body**: Provinciale Staten plenair only (not commissies — those don't hold the votes).

## Status
- [x] Reverse-engineered the GO (Utrecht) voting endpoints, verified structured JSON
- [x] Confirmed multi-vendor reality + completeness/union model
- [ ] Map all 12 provinces → vendor + endpoint
- [ ] Finalize v1 scope, then build collector → dataset → static site
