# Coverage & reliability — what we actually have

What's **live in the dataset** today, how it was obtained, and **how much to trust it**. This is
the "things we DO have" companion to [provinces.md](provinces.md) (feasibility for the rest),
[outreach.md](outreach.md) (who to ask), and [roadmap.md](roadmap.md) (the plan).

> Reliability is the easy thing to forget: every province shows the same green **V** / red **T**,
> but one is read from exact per-member counts and another is *inferred* from parsed free text.
> The column below says which.

## Coverage table

| Province | Vendor | Method | Granularity | Item types | Items | Scope | Reliability |
|---|---|---|---|---|---|---|---|
| **Utrecht** | GO | clean JSON API | per **member** (counts) | motie, amendement, besluit, ordevoorstel | 566 | all (aangenomen + verworpen) | **A — exact** |
| **Noord-Holland** | iBabs | HTML free-text parse | per **fractie** (V/T only) | motie, amendement | 181 | **aangenomen only** | **B — parsed/inferred** |

(Counts as of the last refresh; the weekly Action keeps them current.)

## Reliability tiers

How directly the published data maps to what we display, and how much we infer.

- **A — exact (structured source).** The endpoint returns the vote itself as structured data; we
  normalize, we don't interpret. Exact counts, split votes, abstentions and absences are all real.
  *Utrecht* (GO `/Samenstelling/{fractie}/votings` — per-member tallies).
- **B — parsed / inferred (semi-structured source).** The outcome is published, but as text we must
  parse, and part of the result is *computed* rather than stated. Correct for "which fractie voted
  voor/tegen" on the items present, with the caveats below. *Noord-Holland* (iBabs "Stemverhouding").
- **C — derived / unavailable (not implemented).** Votes exist only in PDFs (GO Flevoland/Drenthe
  besluitenlijsten) or behind an auth-gated map (Notubiz `role_id → fractie`). Either needs new work
  (PDF parsing / a token) and would be lower fidelity. Nothing in the dataset is tier C yet.

## Per-province caveats (what could be wrong, and why)

### Utrecht — tier A
- The dataset mirrors the GO stemgedrag module. The main residual risk is upstream: if a vote was
  mis-recorded in the source, we faithfully reproduce it. Dates are resolved via `meetingId`.
- Practically nothing is inferred on our side.

### Noord-Holland — tier B
Reliable for the headline question ("did fractie X vote voor or tegen this adopted motie?"), but
know these limits before trusting an exact figure:
1. **No exact counts.** Votes are stored `1–0` per fractie, so the "ruwe getallen" toggle shows
   `1–0`, not seat counts, and the agreement %s weight every fractie equally (not by zetels).
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
- **Niet-aangenomen items (iBabs provinces).** Rejected moties/amendementen aren't published
  per-fractie — they'd only be in besluitenlijst/notulen PDFs. Open question whether any province
  exposes them; Zeeland's dedicated "Stemming" report is the best lead.
- **Faction-level provinces lose "ruwe getallen" / exact splits** — inherent to iBabs/Notubiz.
- **Spot-checking.** Tier-B data isn't self-verifying; eyeball a few moties against the portal after
  big parser changes. Method per source is in [data-sources.md](data-sources.md).
