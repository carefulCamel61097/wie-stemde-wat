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

### HTML parsing is fragile — avoid it
The per-motie `voteResultHtml` is rendered HTML (per-member rows). A quick parse already
mis-read the proposer's row. **Prefer the structured `/Samenstelling/{party}/votings`
JSON** (clean per-party counts) over scraping the popup HTML.
