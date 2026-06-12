# Data sources & API findings

Everything below was verified live against
`https://www.stateninformatie.provincie-utrecht.nl` (June 2026). All endpoints are
**public, no authentication, JSON**.

## 1. The platform
- The site runs on **GemeenteOplossingen (GO)** — footer: "een oplossing van GO".
- Voting is GO's **"GO. stemgedrag"** module: it reads the digital voting boxes from
  meetings and publishes the results.
- Data owner = **Provincie Utrecht / Statengriffie**; GO = vendor/host/processor.
- Utrecht's Open Data statement: https://www.stateninformatie.provincie-utrecht.nl/over-deze-site/Open-Data
  ("all data … retrievable without restrictions").

## 2. Two layers of API

### (a) The *documented* Open (Raads/Staten)Informatie API — structure, NOT votes
- Base: `https://www.stateninformatie.provincie-utrecht.nl/api/v2/`
- This follows the national **VNG Open Raads-/Stateninformatie** spec
  (docs: http://docs.openraadsinformatie.nl/ ; spec: https://github.com/VNG-Realisatie/ODS-Open-Raadsinformatie).
- Response envelope: `{"status":"OK","code":200,"messages":[],"result":{...}}`
- Useful endpoints (verified):
  - `GET /api/v2/meetings?limit=&offset=` — meetings (totalCount ~1788).
    Each: `id, date, startTime, dmu{id,name}, location, url`.
  - `GET /api/v2/meetings/{id}` — single meeting (note: does **not** inline agenda items).
  - `GET /api/v2/dmus` — *organen* (PS + committees), e.g. `14 = Provinciale Staten`.
  - `GET /api/v2/groups?limit=60` — fracties + other bodies. `type:"Fractie"` = parties.
  - `GET /api/v2/events`, `/documents`, `/persons`, `/attachments`, `/positions`, `/roles`.
- **This documented API exposes meetings/documents/people/orgs but has NO votings/
  stemming endpoint.** That's why it looked like the votes weren't available.

### (b) The website's own AJAX endpoints — these DO have the votes
These power the site's UI. Undocumented in the open-data spec, but fully public.
Discovered by reading the site JS
(`/site/default2020/script/employees/votings.js` and `components/VotingModal.js`).
A code comment in `votings.js` even grumbles "seems like bad API design" — i.e. these
are internal endpoints, not a deliberate secret.

**Best building block — per party, all moties (clean structured JSON):**
```
GET /Samenstelling/{party-slug}/votings
```
Example: `/Samenstelling/bbb/votings`. Returns `items` keyed by year; each entry:
```json
{
  "votingId": 28163,
  "description": "M26-40a Van begroten naar realiseren, ingediend door UtrechtNu! & SGP",
  "documentId": 64815, "meetingItemId": 25015, "meetingId": 11125,
  "voteResult": {
    "name": "accepted", "label": "Aangenomen",
    "voteCounts": { "agree": 6, "disagree": 0, "absent": 0, "abstain": 0 }
  }
}
```
Here `voteCounts` is **this party's own** vote split (BBB: 6 voor, 0 tegen → "voor").
`updatedAt` gives the date. No HTML parsing needed.

**Cross-party detail for a single motie (the "i" popup):**
```
GET /vergaderingen/stemmingen/{type}/{ref}
    type ∈ { document | agendapunt | vergadering }   (ref = documentId / meetingItemId / meetingId)
```
Example: `/vergaderingen/stemmingen/document/64815`. Returns:
- `groups[]` — all fracties/bodies (id, name)
- `votes[]` — each: `votingId, title, result, voteResult{agree,disagree,abstain,absent}`
  (overall totals, structured) **plus** `voteResultHtml` (rendered per-party table — HTML only).
- ⚠️ In this endpoint the *per-party* breakdown is only inside `voteResultHtml`. For
  structured per-party data prefer endpoint (a) above per party instead of parsing HTML.

Other party AJAX tabs (same pattern): `/Samenstelling/{slug}/activities`,
`/Samenstelling/{slug}/speakerfragments`, `/Samenstelling/{slug}/{year}`.

### Completeness model (VERIFIED — important)
The breakdown is recorded **per individual member** (the popup lists each member by name
plus the party totals) → voting is captured at member level (digital voting boxes /
hoofdelijke registratie).

For motie `document/64815` the breakdown listed **14 parties / 44 seats**, but PS Utrecht
has **49 seats**. Parties that were entirely absent (e.g. PVV, JA21) **do not appear at
all** — neither in that motie's breakdown nor (by the same logic) in their own
`/votings` list.

Consequences for our data model:
- **No single party endpoint is a complete motie list.** Build the master motie list as
  the **UNION of `votingId` across ALL parties' `/votings`** (a motie always has ≥1 party
  present, so the union is complete).
- A motie present in the union but absent from party P's list ⇒ **P was afwezig** for it
  (render blank/grey).
- Per-member absence within a present party is captured by a reduced `(N personen)` /
  lower counts. Abstentions are captured by `voteCounts.abstain`.
- `votingId` is the stable global key (same id appears in the party list and the
  cross-party detail). `documentId`/`meetingItemId`/`meetingId` also link out.
- For accurate **dates**, map each entry's `meetingId` → `GET /api/v2/meetings/{id}.date`
  (the `updatedAt` field is only an approximation).

## 3. Fracties (parties) — group ids (type "Fractie")
Slugs for the `/Samenstelling/{slug}/votings` call are the lowercased site slugs
(e.g. `bbb`, `vvd`, `groenlinks`, `d66`, `volt`, `pvdd`/"partij-voor-de-dieren" — to verify).

| id | party |
|----|-------|
| 443 | BBB |
| 164 | VVD |
| 165 | GroenLinks |
| 167 | D66 |
| 168 | CDA |
| 163 | PvdA |
| 169 | SP |
| 170 | ChristenUnie |
| 171 | Partij voor de Dieren |
| 172 | PVV |
| 166 | SGP |
| 173 | 50PLUS |
| 265 | Forum voor Democratie |
| 266 | DENK |
| 365 | JA21 |
| 444 | Volt |
| 539 | UtrechtNu! |
| 436 | BVNL |
| 425 | Socialisten Utrecht |
| 357 | Lijst Bittich |
| 358 | Onafhankelijke Statenfractie Utrecht |
| 390 | Gedeputeerde Staten (not a real fractie) |

(Current vs historical parties differ per period; the `/votings` data spans many years.)

## 4. Alternative source (not chosen)
- **Open Raadsinformatie / OpenBesluitvorming** (Open State Foundation + VNG):
  https://zoek.openraadsinformatie.nl/ , https://openbesluitvorming.nl/ — has a public
  (Elasticsearch) API and indexes moties/voting nationally. UI not ideal; Utrecht's own
  API is more direct, so we use that.

## 5. Build plan (no scraping)
1. Get the list of party slugs (from `/Samenstelling` page or the table above).
2. For each party: `GET /Samenstelling/{slug}/votings` → collect every motie with that
   party's `voteCounts`.
3. Merge per motie (key on `votingId` / `documentId`) into a matrix:
   rows = moties (date, code like "M26-40a", description, overall result),
   columns = parties, cell = *voor* / *tegen* / *onthouden* / *afwezig* / split.
   - "mostly voor" = agree > disagree; "mostly tegen" = disagree > agree.
4. Export as CSV and/or a Markdown table and/or a small static HTML page.
5. Be polite: cache responses, add a small delay between requests.

## Quick test commands (PowerShell)
```powershell
# one party, all moties
Invoke-RestMethod "https://www.stateninformatie.provincie-utrecht.nl/Samenstelling/bbb/votings"

# one motie, all parties (overall totals + HTML breakdown)
Invoke-RestMethod "https://www.stateninformatie.provincie-utrecht.nl/vergaderingen/stemmingen/document/64815"
```

## 6. Multi-province / multi-vendor (scope change)
Provinces do NOT share one platform. There is no uniform endpoint across all 12.
Known so far (to be completed for all 12):

| Province | Vendor | Portal (example) |
|----------|--------|------------------|
| Utrecht | **GemeenteOplossingen (GO)** | stateninformatie.provincie-utrecht.nl |
| Flevoland | **GO** (co-creation project) | (GO — reuse our adapter) |
| Noord-Holland | **iBabs** | noordholland.bestuurlijkeinformatie.nl |
| Overijssel | **Notubiz** | overijssel.notubiz.nl |
| Gelderland | ? (gelderland.stateninformatie.nl) | to verify |
| Drenthe, Fryslân, Groningen, Limburg, Noord-Brabant, Zeeland, Zuid-Holland | ? | TODO |

⇒ Architecture: **one adapter per vendor** (GO / iBabs / Notubiz), each normalizing to a
common schema. Our Utrecht reverse-engineering = the **GO adapter** (works for Flevoland
too, same software).

- **iBabs**: has an API + open data (data.overheid.nl "ibabs-online"). Adapter TODO.
- **Notubiz**: public API at `api.notubiz.nl` (no formal public docs). Has a stemgedrag /
  "Politiek Portret" feature. Adapter TODO.

### Unified national source (fallback, NOT primary)
**OpenBesluitvorming / Open Stateninformatie** (Open State Foundation + VNG):
- ElasticSearch API: `https://api.openraadsinformatie.nl/v1/elastic/`
- Aggregates ~294 municipalities + **only 6 provinces**; standardized schema.
- BUT provincial **vote/stemming** coverage is historically weak (Open State:
  "regional voting records untraceable"). Good for documents, unreliable for votes.
- Use as a cross-check / fallback, not the source of the vote data.

## 7. iBabs adapter — endpoints (CRACKED, Noord-Holland)
The iBabs publieksportaal (`{prov}.bestuurlijkeinformatie.nl`) is an ASP.NET SPA with a
DataTables server-side table. Per-fractie votes ARE retrievable (no auth):

- **Reports list / GUIDs**: `GET /Reports` → each report = `/Reports/Details/{guid}`.
  NH **Moties** report = `84a8ac43-1424-48a9-8a1a-0c0bbcdfd8ed`; Zeeland **Stemming** report =
  `8f77ee0a-822e-4cbe-8acc-7ff35488c8ac`.
- **Motie list (clean JSON)**:
  `POST /Reports/GetReportData/{reportGuid}` — body `draw=1&start=0&length=1000`,
  header `X-Requested-With: XMLHttpRequest`. (GUID is in the PATH; GET 404s; must be POST.)
  Returns `{draw, recordsTotal, data:[ {DT_RowId, identity, ingediendindatum (dd-mm-yyyy),
  motienummer, title, fracties (=INDIENERS, not votes), status, behandelenin} ]}`.
- **Per-fractie votes**: `GET /Reports/Item/{DT_RowId}` → server-rendered HTML with a
  **"Stemverhouding"** field, e.g. `Tegen: VVD /BBB /JA21. Voor: overige fracties (X afwezig).`

Stemverhouding parsing notes (free text — handle all):
- `Unaniem` → all parties voor.
- `Tegen: A /B /C. Voor: overige fracties.` (and the reverse) → one side listed, other = the rest.
- separators vary: `/`, `/ `, `, `. Names: VVD, BBB, JA21, PVV, FvD, PvdD, SP, 50PLUS, Volt,
  ChristenUnie/CU, GroenLinks, PvdA, D66, …  (need an abbreviation→canonical map).
- `(… afwezig)` notes → afwezig fractions (exclude from "overige fracties").
- **"overige fracties" must be expanded vs the council composition** → scope to current term and
  build the party universe from the data (+ the report's `fracties` filter options). Composition
  changes across terms, so a static all-time union is wrong — term-scope it.
- Granularity = per-fractie V/T only (no counts) → store agree/disagree = 1/0; "ruwe getallen"
  and split-vote degrade gracefully for iBabs provinces.

### Implementation notes (Noord-Holland — adapter BUILT, `collect_ibabs`)
What the live build surfaced beyond the recipe above:
- **Date**: the detail page has a `Datum PS` field (dd-mm-yyyy) = the plenary vote date — use it
  for term-scoping (`>= 2023-03-29`), not the list's `ingediendindatum`. Pre-fetch only rows
  with `ingediendindatum` year `>= term-1` to avoid pulling all ~800 detail pages.
- **Multiple reports**: `GET /Reports` lists several (Moties, **Amendementen**, Ingekomen stukken,
  Toezeggingen, Schriftelijke/Technische vragen, …). Only **Moties** + **Amendementen** carry a
  Stemverhouding. The adapter takes a `reports: [{guid, type}]` list and unions them (each report
  gets its own `id_base` since the `identity` counter restarts per report). NH ships moties +
  amendementen (141 + 40 in-term).
- **Scope — only adopted items**: both registers are *afdoening*-trackers → **only `Aangenomen`
  moties/amendementen** (every in-term row, no verworpen). So the **niet-aangenomen** moties/
  amendementen are NOT published per-fractie anywhere on the portal — they'd only be in the
  besluitenlijst/notulen PDFs. Disclosed to users via `meta.note`. (Zeeland's dedicated "Stemming"
  report may include rejected too — check when adding it.)
- **Result source differs per report**: the Moties list row has a `status` field; the Amendementen
  list/detail has **none** — the outcome sits in the *attachment filename* ("A8-2026 **AANGENOMEN** …").
  Parse that keyword. **Do NOT derive the result from the vote tally** — we count *fracties*, not
  *zetels*, so a close vote (e.g. 8 small parties tegen vs 7 large voor) flips the wrong way.
- **UA**: the collector's plain UA works against iBabs (HTTP 200) — no browser spoofing needed
  in GitHub Actions; POST `GetReportData` needs `Content-Type: application/x-www-form-urlencoded`.
- **Free-text quirks the parser must handle** (all real, in-term):
  - `Tegen: JA 21 /PVV /50PLUS` — abbreviations with stray spaces ("JA 21" → JA21).
  - separators mix `/`, `, `, ` en `, and even **space-only** ("Tegen: PVV FvD") → tokenize
    space lists greedily, longest-alias-first, so "Fractie De Weerdt" stays whole.
  - **glued labels**: `…FvD, SPVerdeeld gestemd: VVD, PvdAVoor: Overige fracties` — un-glue with
    a regex that inserts a space before `Voor/Tegen/Afwezig:` / `Verdeeld gestemd:` stuck to a name.
  - **`Verdeeld gestemd:` clause** = fracties that split their own vote → store `agree==disagree`
    (renders as "O" + split-dot).
- **"overige fracties" expansion** = term party universe (built data-driven from every explicitly
  named fractie) **minus afwezig minus split**. Composition shifts *within* a term too: gate each
  fractie by a `first_seen` date (earliest time it's named on a side, noted afwezig, or appears as
  indiener) so a mid-term splinter (NH's **Fractie De Weerdt**) isn't back-filled into older moties.
- **Frontend contract**: `id` must be a number (the table coerces `+dataset.id` for pinning) →
  use the list `identity` int. Pick the huisstijl `accent` from `/Base/SiteCss` `--button-color`
  (NH = `#2891e0`). Party slugs reuse the existing `ABBR` map where they slugify the same.

### Other iBabs provinces (probed)
Not every iBabs portal is like NH — the vote *format* varies, and two are dead ends:
- **Limburg** — BEST iBabs province (built). Detail pages have a structured **"Stemmen"** field
  (not "Stemverhouding"): `<div class="vote-summary-legend-{in-favour|against}"><div class="text">
  Fractie (Statenleden) (N), …</div>` — i.e. **per-fractie member counts** for the voor and tegen
  sides (tier A, like Utrecht). A fractie on both sides = a real split. The register **includes
  verworpen** (status field: Aangenomen/Verworpen/Ingetrokken/Aangehouden). Date = list `datum`.
  321 in-term items (271 moties + 50 amendementen). Moties decided *bij acclamatie* (no hoofdelijke
  stemming) have an empty Stemmen field → skipped. Reports: Moties `0493fdd4-…`, Amendementen
  `34a4e0ce-…`. Handled by the adapter's `votes: "stemmen"` format.
- **Noord-Brabant** — Moties register has the status (incl. verworpen) but **no per-fractie
  breakdown** on the detail page → unusable for our table (outcome only).
- **Zeeland** — all three registers (Moties, Amendementen, **Stemming** `8f77ee0a-…`) return
  **0 rows**. Empty; nothing to collect.

⇒ The adapter now branches on a province `votes` format: `"stemverhouding"` (NH free-text,
faction-level, inference) vs `"stemmen"` (Limburg structured, per-member counts, exact).

### HTML parsing is fragile — avoid it
The per-motie `voteResultHtml` is rendered HTML (per-member rows). A quick parse already
mis-read the proposer's row. **Prefer the structured `/Samenstelling/{party}/votings`
JSON** (clean per-party counts) over scraping the popup HTML.

## 8. Tweede Kamer — OData API (CRACKED, verified 2026-06-11)
The Tweede Kamer publishes a first-class **OData v4** open-data API. No auth, no token, JSON,
and it carries **per-fractie votes with exact seat counts** → tier A (like Utrecht/Limburg),
*incl. verworpen*. Far cleaner than any provincial portal. This is a **new category**, not a
province (see roadmap Phase 4).

- **Base:** `https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/`
  (service doc lists entity sets; `$metadata` has the full schema). Append `&$format=json`.
- **UA:** plain works (no browser spoof needed) — fine for GitHub Actions.

### The vote chain
```
Stemming ──Besluit_Id──▶ Besluit ──Agendapunt──▶ Agendapunt ──Activiteit_Id──▶ Activiteit
   │                        │                                                      └─ Datum (vote date)
   │                        └──Zaak[] (the motie/amendement/wetsvoorstel)
   └─ per-fractie vote row
```
- **`Stemming`** (one row per fractie per besluit): `Soort` (`Voor` | `Tegen` | `Niet deelgenomen` |
  null), **`FractieGrootte`** (seat count → exact tallies), `ActorFractie` (display name AT vote
  time), `Fractie_Id`, `Besluit_Id`. `Persoon_Id` is set only for the rare hoofdelijke (per-person)
  votes — for fractie votes it's null.
- **`Besluit`**: `BesluitSoort` (outcome, see below), `BesluitTekst` ("Aangenomen."), `Agendapunt_Id`.
- **`Zaak`** (besluit→Zaak is a *collection* nav): `Soort` (`Motie` | `Amendement` | `Wetgeving` | …),
  `Nummer` ("2024Z15642"), `Onderwerp` (readable title "Motie van het lid X over Y"), `Vergaderjaar`.
- **`Activiteit`** (via `Agendapunt`): `Soort` "Stemmingen", **`Datum`** = the plenary vote date.

### Efficient fetch (≈12 requests, not 3k)
OData `$expand` inlines children, and nested navigation is **filterable**. One paged query pulls
everything:
```
GET /Besluit
  ?$filter=startswith(BesluitSoort,'Stemmen')
           and Agendapunt/Activiteit/Datum ge 2025-11-13T00:00:00Z
           and Stemming/any()
           and Zaak/any(z: z/Soort eq 'Motie' or z/Soort eq 'Amendement' or z/Soort eq 'Wetgeving')
  &$expand=Stemming($select=ActorFractie,Soort,FractieGrootte),
           Zaak($select=Nummer,Soort,Onderwerp),
           Agendapunt($expand=Activiteit($select=Datum))
  &$select=Id,BesluitSoort,BesluitTekst
  &$format=json
```
Server **page cap = 250 rows**; follow `@odata.nextLink` until absent. (`@odata.count` via
`$count=true` for totals.)

### Scope, outcomes, mapping (decisions)
- **Current term = on/after `2025-11-13`** (first stemming of the Kamer installed after the
  29 Oct 2025 election; constituerende vergadering 12 Nov 2025). The *old* Kamer kept voting between
  election day and installation — date-gating at 11-13 excludes those old-composition votes and keeps
  fractie sizes consistent. Consistent with the locked "current term only" decision.
- **Volume (verified 2026-06-11):** 3,450 `Stemmen*` besluiten since term start; of those **3,009 have
  a real roll-call** (`Stemming/any()`), **2,945** of which link to a Motie/Amendement/Wetgeving — that
  is our keepable set. (Moties 2,884 · amendementen 418 · wetgeving 64 across the term.) ~6 MB pretty
  → **write `tweede-kamer.json` compact (~3 MB)**. Frontend perf with ~3k rows × ~18 cols is a watch
  item (provinces are 181–566 rows); revisit virtualization/pagination if sluggish.
- **Keep only roll-call besluiten** (`Stemming/any()`). The many non-vote `BesluitSoort` values
  (`aangehouden`, `ingetrokken`, `uitstellen`, `vervallen`, **`zonder stemming aannemen`**) have no
  `Stemming` rows and drop out naturally — don't rely on the label, rely on the presence of votes.
- **Outcome** from `BesluitSoort`: `Stemmen - aangenomen|goedgekeurd|vastgesteld` → accepted;
  `Stemmen - verworpen|niet aangenomen` → rejected; `Stemmen - gestaakt` → tie (staking van stemmen).
- **Vote → counts:** `Voor` → `agree += FractieGrootte`, `Tegen` → `disagree += FractieGrootte`,
  `Niet deelgenomen`/null → abstain/absent. A fractie with both Voor and Tegen rows = a real split.
  Self-contained per besluit (no "overige fracties" inference) → granularity `member`, tier A.
- **Mid-term composition quirks** (handle/note, not blocking): `ActorFractie` is the name *at vote
  time*, so renames create separate columns — e.g. **GroenLinks-PvdA → "Progressief Nederland" (PRO)
  on 2026-06-09**; splinters **Groep Markuszower** (PVV, 2026-01-20) and **Keijzer**/"Lid Keijzer"
  (BBB, 2026-02-24). A small alias map can merge a pure rename (GL-PvdA ↔ PRO) into one column.
  `Fractie.AantalZetels` reflects *current* seats (post-splinter), so prefer the per-vote
  `FractieGrootte`, never the Fractie table, for tallies.

## 9. Eerste Kamer — HTML only (PROBED 2026-06-12, feasibility = GO, tier B)
The Eerste Kamer is a **separate system** from the TK OData and has **no machine API**: no
`gegevensmagazijn.eerstekamer.nl` / `opendata.eerstekamer.nl` host (DNS fails), no `/api`, no
OData, no SPARQL on the site. Everything is **server-rendered HTML on `www.eerstekamer.nl`** (the
PARLIS CMS). Per-fractie positions ARE published though — verified live. Granularity = **faction-
level V/T, NO seat counts** (EK votes *bij zitten en opstaan* — the chair declares the result, no
tallies; exact numbers only on a rare *hoofdelijke* stemming) → **tier B** (like Noord-Holland, but
see below: both sides are named explicitly, so NO "overige fracties" inference → more reliable than NH).
- **UA:** browser User-Agent works; plain may be throttled — send a browser UA (GitHub Actions OK).
- **Fracties (current EK term, 2023–2027): 20** — the 13 landelijke (VVD, GroenLinks-PvdA, BBB, D66,
  PVV, CDA, SP, ChristenUnie, PvdD, JA21, SGP, Volt, FVD, OPNL, 50PLUS) plus EK splinter fracties
  (Fractie-Beukering, -Van Gasteren, -Van de Sanden, -Visseren-Hamakers, -Walenkamp). Display name =
  `<X>-fractie`; slug at `/fractie/<slug>` (e.g. `/fractie/volt`, `/fractie/partij_voor_de_vrijheid`).

### Two HTML surfaces carry the per-fractie vote
1. **`/stemmingen_fractiegewijs`** — *structured, no NLP.* One collapsible section **per fractie**;
   a summary votebox (all-time `Voor / Tegen / Verdeeld` totals) + a `<ul class="stemlijst">` listing
   **every item that fractie voted on**, each `<li>` carrying: a thumb img `alt="Voor"|"Tegen"` (the
   fractie's position), the date (link), the type+result in parens (`(Hamerstuk)`,
   `(Stemming bij zitten en opstaan, aangenomen|verworpen)`), the title, and the dossier link
   (`/wetsvoorstel/36264_…` or `/kamerstukdossier/…`). **Paginated ~500 items/section.** Pro: no
   free-text parsing. Con: the link is the day's verslagdeel, **not unique per stemming** — two
   stemmingen under the same dossier/day/result (e.g. an amendement + the wetsvoorstel) are hard to
   tell apart → join-key ambiguity.
2. **The verslag page** (`/verslagdeel/{yyyymmdd}/{slug}` or `/id/{vid}/verslagdeel/…`) — *free-text,
   but both sides named.* Contains one chair sentence **per stemming**:
   `"Ik constateer dat de leden van de fracties van <VOOR-lijst> voor … hebben gestemd en de leden van
   de fracties van <TEGEN-lijst> ertegen, zodat het is <aangenomen|verworpen>."` Both sides enumerated
   (no "overige fracties" guess). A prototype parser mapped all sides to the 20-fractie universe
   cleanly (only fix needed: don't strip "de/het" inside names like *Fractie-Van de Sanden*).

### Vote types & volume
- **Hamerstuk** = passed without a vote (no objection) → uncontested, all fracties effectively voor.
- **Stemming bij zitten en opstaan** = the real (contested) votes; per-fractie split recorded (no counts).
- **Hoofdelijke stemming** = rare, per-member by name (aggregate to fractie; best-effort).
- **Index page:** `/stemmingen_per_vergaderdag?filter=alles` lists each stemming as a row (date, title,
  type, result, link), **paginated 25/page** via `start_006=` + `dlastinprev=YYYY-MM-DD`. Recent sample:
  ~25 stemmingen / 6 weeks (16 zitten-en-opstaan + 5 hamerstuk per page) → est. **~600–700 stemmingen
  over the 2023–2027 term** (between NH's 181 and Utrecht's 566 in scale — fine for the frontend).
- **Term boundary:** current EK installed **13 June 2023** (elected by the March 2023 PS). Scope votes
  `>= 2023-06-13`. (Note: EK term ≠ TK term — TK is 2025–heden, EK is 2023–2027.)
- **Item types:** wetsvoorstellen, moties, amendementen (+ brieven/overig — classify from the dossier link).

### Recommended build (collect_ek)
**Stemming-first** (preserves unique identity + metadata): walk `/stemmingen_per_vergaderdag?filter=alles`
pages back to 2023-06-13 → per row get date/title/dossier/type/result; for **zitten-en-opstaan** rows
fetch the verslag and parse the matching `Ik constateer …` sentence (both sides → per-fractie V/T);
**hamerstuk** rows = unanimous voor (or mark uncontested). Write `data/eerste-kamer.json` (same schema,
votes per fractie `agree/disagree = 1/0`, `granularity: "fractie"`), category `eerste-kamer`, single
scope. Parser caveats to handle: leading "de/het" inside fractie names, separator variants
(`,` / ` en `), splinter `first_seen` gating, hoofdelijke (per-member) rare case. Tier B → set
`meta.note` like NH; document in [coverage.md](coverage.md).
