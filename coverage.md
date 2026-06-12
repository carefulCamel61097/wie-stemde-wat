# Coverage & reliability — what we actually have

What's **live in the dataset** today, how it was obtained, and **how much to trust it**. This is
the "things we DO have" companion to [provinces.md](provinces.md) (feasibility for the rest),
[outreach.md](outreach.md) (who to ask), and [roadmap.md](roadmap.md) (the plan).

> Reliability is the easy thing to forget: every province shows the same green **V** / red **T**,
> but one is read from exact per-member counts and another is *inferred* from parsed free text.
> The column below says which.

## Coverage table

| Scope | Category | Vendor | Method | Granularity | Item types | Items | Scope of items | Reliability |
|---|---|---|---|---|---|---|---|---|
| **Tweede Kamer** | Tweede Kamer | TK OData | clean OData v4 API | per **fractie** (zetels) | motie, amendement, wetsvoorstel | 2945 | **aangenomen + verworpen** | **A — exact** |
| **Utrecht** | Prov. Staten | GO | clean JSON API | per **member** (counts) | motie, amendement, besluit, ordevoorstel | 566 | all (aangenomen + verworpen) | **A — exact** |
| **Limburg** | Prov. Staten | iBabs | HTML structured parse | per **member** (counts) | motie, amendement | 321 | **aangenomen + verworpen** | **A — exact** |
| **Noord-Holland** | Prov. Staten | iBabs | HTML free-text parse | per **fractie** (V/T only) | motie, amendement | 181 | **aangenomen only** | **B — parsed/inferred** |

(Counts as of the last refresh; the weekly Action keeps them current. TK = current term, 2025–heden.)

> Note: vendor ≠ reliability. Both Limburg and Noord-Holland run iBabs, but Limburg's portal
> publishes structured per-member vote counts (tier A) while NH publishes only free-text faction
> outcomes (tier B). The portal's *vote format* decides the tier, not the vendor.

## Reliability tiers

How directly the published data maps to what we display, and how much we infer.

- **A — exact (structured source).** The source gives the vote itself as structured data; we
  normalize, we don't interpret. Exact counts and real split votes; minimal inference.
  *Tweede Kamer* (OData `Stemming` — per-fractie `Soort` + `FractieGrootte` seat counts),
  *Utrecht* (GO JSON, per-member tallies) and *Limburg* (iBabs "Stemmen" field — per-fractie member
  counts for the voor/tegen sides; a fractie on both sides is a real split).
- **B — parsed / inferred (semi-structured source).** The outcome is published, but as text we must
  parse, and part of the result is *computed* rather than stated. Correct for "which fractie voted
  voor/tegen" on the items present, with the caveats below. *Noord-Holland* (iBabs "Stemverhouding").
- **C — derived / unavailable (not implemented).** Votes exist only in PDFs (GO Flevoland/Drenthe
  besluitenlijsten) or behind an auth-gated map (Notubiz `role_id → fractie`). Either needs new work
  (PDF parsing / a token) and would be lower fidelity. Nothing in the dataset is tier C yet.

## Per-scope caveats (what could be wrong, and why)

### Tweede Kamer — tier A
- Votes come straight from the OData `Stemming` entity: per fractie a `Soort` (Voor/Tegen/Niet
  deelgenomen) and `FractieGrootte` (seat count). Exact tallies, self-contained per besluit — nothing
  inferred (unlike NH). Includes **verworpen**. We keep only besluiten with an actual roll-call
  (`Stemming/any()`), so items decided *zonder stemming* / aangehouden / ingetrokken drop out.
- **Three vote shapes, one counting rule** (verified — each besluit's seats sum to ≤150):
  a *block* vote = one row per fractie (use `FractieGrootte`); a *hoofdelijke* stemming = one row
  **per member** (each carries the full fractie size — count 1 per row, not the size); *block +
  aantekening* = a block row plus per-member rows for deviating members (count the members as 1 and
  subtract them from the block, so they aren't double-counted). A fractie whose members split on a
  hoofdelijke vote correctly shows a real split (V + dot, or O).
- **Rare upstream inconsistencies.** The official `BesluitSoort` is the source of truth for the
  outcome and we mirror it; on ~1 item in ~3,000 it disagrees with the seat tally (e.g. a motie
  marked *aangenomen* that tallies 71–79). We don't "correct" the source — the per-fractie positions
  are still shown verbatim. 75–75 ties recorded as *verworpen* are genuine, not errors.
- **Term scope:** current Kamer only (votes on/after 2025-11-13, the first stemming after the Oct 2025
  election). Old-composition votes cast before installation are excluded so fractie sizes stay consistent.
- **Mid-term composition:** `ActorFractie` is the name *at vote time*. We merge the pure rename
  GroenLinks-PvdA → "Progressief Nederland" into one column; splinters (Groep Markuszower, Keijzer)
  are their own columns — accurate, if visually busier. `Persoon_Id`-level (hoofdelijke) votes aren't
  split out; we aggregate to the fractie.
- **Volume:** ~2,945 stemmingen → the data file is ~3 MB (written minified) and the table renders
  ~3k rows × ~18 columns. Watch frontend performance; revisit pagination/virtualization if it drags.

### Utrecht — tier A
- The dataset mirrors the GO stemgedrag module. The main residual risk is upstream: if a vote was
  mis-recorded in the source, we faithfully reproduce it. Dates are resolved via `meetingId`.
- Practically nothing is inferred on our side.

### Limburg — tier A
- The "Stemmen" field lists each fractie with its member count on the voor and tegen sides, so
  counts and splits are exact (27 in-term moties have a real fractie split). **Includes verworpen**
  moties and amendementen — the only iBabs province so far with rejected items.
- The one gap: moties/amendementen decided **without a hoofdelijke stemming** (bij acclamatie /
  handopsteken) carry no per-fractie tally and are skipped. In practice this only drops the
  ingetrokken/aangehouden items; essentially all *decided* moties have a recorded breakdown.
- Local fracties (LOKAAL-LIMBURG, Horizon, oos limburg, SVL) pass through un-aliased.

### Noord-Holland — tier B
Reliable for the headline question ("did fractie X vote voor or tegen this adopted motie?"), but
know these limits before trusting an exact figure:
1. **No exact counts.** Votes are stored `1–0` per fractie. The UI reads `meta.granularity:
   "fractie"` and **hides the "ruwe getallen" toggle** (and describes cells in words, not "1 voor
   0 tegen") so the missing counts aren't shown as if real. Agreement %s weight every fractie
   equally (not by zetels).
2. **"Overige fracties" is inferred, not stated.** The losing side is named; the winning side is
   "overige fracties", which we expand against a *computed* party universe (built from the data)
   minus afwezig/split, with a `first_seen` gate for mid-term splinters. This is the layer most
   likely to hide a subtle error — it's an assumption about who was in the room.
3. **Free-text parsing.** Stemverhouding is inconsistent prose (glued labels, stray spaces,
   "Verdeeld gestemd:" clauses). The parser handles every form seen so far; a *novel* phrasing
   could be mis-read or skipped (the collector logs "no parseable vote" counts — watch them).
4. **Splits/abstentions are lossy.** A split shows only when the portal writes "Verdeeld gestemd";
   abstentions aren't represented at fractie level.
5. **Adopted only.** The iBabs registers track *aangenomen* moties/amendementen — **verworpen items
   are absent entirely** (not published per-fractie anywhere on the portal; see the gap below).

## Known gaps to revisit
- **Niet-aangenomen items (some iBabs provinces).** Limburg publishes verworpen items; **Noord-Holland
  does not** (its registers are adopted-only — rejected ones live only in besluitenlijst/notulen PDFs).
  So the gap is portal-specific, not vendor-wide. (Zeeland's "Stemming" report turned out **empty**;
  Noord-Brabant publishes outcomes but no per-fractie breakdown — neither is usable yet.)
- **Faction-level provinces lose "ruwe getallen" / exact splits** — inherent to iBabs/Notubiz.
- **Spot-checking.** Tier-B data isn't self-verifying; eyeball a few moties against the portal after
  big parser changes. Method per source is in [data-sources.md](data-sources.md).
