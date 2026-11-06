# Outreach — draft e-mails to unlock more provinces

Two low-cost asks that could turn hard provinces into easy ones. See [provinces.md](provinces.md)
for why. Both are about **open data**, so there's good precedent (Utrecht already does this).

---

## 1. Notubiz — request an open-data API token
> **✅ Sent 2026-06-10.** Awaiting reply. If granted, build the Notubiz adapter (see roadmap NEXT).
> **Follow-up:** if silent by **~17 June** (≈1 week), send the nudge below. A company support inbox
> usually moves within days, so a short reminder mostly serves to surface a filtered/missed mail.
>
> _Reminder draft (reply on the original thread, keeping the first mail quoted below):_
> > Beste Notubiz,
> >
> > Vorige week (10 juni) stuurde ik onderstaand verzoek om een open-data API-token voor de stemdata
> > van de Provinciale Staten. Ik begrijp dat het druk kan zijn — zou u kunnen laten weten of dit
> > mogelijk is, of mij naar de juiste persoon kunnen verwijzen? Alvast dank!
> >
> > Met vriendelijke groet, [naam]

**Unlocks (if granted):** Fryslân, Groningen, Gelderland, Zuid-Holland, Overijssel (5 provinces).
**Why:** `api.notubiz.nl/agenda_items/votings` already gives outcomes + roll-call publicly, but
votes are keyed by `role_id` and the `role_id → fractie` map sits behind the auth-gated `/roles`
endpoint. A token lets us group votes per party.

**To:** Notubiz support / open data (info@notubiz.nl)
**Onderwerp:** Verzoek om API-token voor open stemdata (Provinciale Staten)

> Beste Notubiz,
>
> Ik bouw een open, non-commercieel overzicht van het stemgedrag **per fractie** in de
> Provinciale Staten (open data, gratis toegankelijk). Via `api.notubiz.nl/agenda_items/votings`
> kan ik de uitslagen en de hoofdelijke stemmingen (`role_id` + stem) ophalen, maar de koppeling
> `role_id → fractie` zit achter het `/roles`-endpoint, dat authenticatie vereist.
>
> Zouden jullie mij een API-token kunnen verstrekken voor open-data gebruik, zodat ik
> `/roles` (`field_id=105`, per `meeting_id`) kan opvragen om de stemmen per fractie te groeperen?
> Het gaat om de provincies die op jullie platform draaien: Fryslân, Groningen, Gelderland,
> Zuid-Holland en Overijssel.
>
> Het project is open en non-commercieel; u kunt het hier bekijken:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
> (Provincie Utrecht, Noord-Holland en Limburg zijn er al in opgenomen.)
>
> Alvast hartelijk dank,
> [naam]

> **Tip:** de twee links (website + repo) zijn het overtuigendst — ze laten zien dat het een echt,
> open, non-commercieel project is. Dat helpt meer dan alleen het technische endpoint. Vul je eigen
> naam in bij `[naam]`.

---

## 2. Statengriffie Flevoland & Drenthe — enable the GO stemgedrag module
> **✅ DRENTHE DONE (live 2026-07-05).** Mailed 2026-06-11, nudged 2026-06-29; the Statengriffie had
> GemeenteOplossingen investigate. Verdict: the votes were **published all along, at a different path**
> (`/Leden/{slug}/votings`, not Utrecht's `/Samenstelling/...`) — so no module toggle was even needed;
> config-only on our side. Drenthe = 443 stemmingen, 15 fracties, tier A. See data-sources.md §2b + roadmap Phase 8.
>
> **⏳ FLEVOLAND — second nudge sent 2026-11-06.** Still silent after ~5 months. This nudge leads with the
> **Drenthe finding** (same vendor: the votes were published all along at `/Leden/...`, nothing had to be
> switched on) and asks only one concrete question — which of the two paths is active on their install —
> which GemeenteOplossingen can answer in a minute. If this stays silent, park Flevoland rather than
> nudging a fourth time. Original thread below.
>
> `griffie@flevoland.nl`, mailed 2026-06-11, followed up
> 2026-06-29, no reply. Same GO ask. **Given Drenthe: explicitly ask them to have GO check the `/Leden/...`
> path** — the votes may already exist there. Get any reply moving **before the zomerreces (~mid-July)**;
> after that, expect nothing until late Aug/Sept.
>
> _Reminder draft (reply on each original thread):_
> > Geachte Statengriffie,
> >
> > Op 11 juni stuurde ik onderstaand verzoek over het publiceren van het stemgedrag per fractie als
> > open data (zoals provincie Utrecht dat doet). Zou u kunnen aangeven of dit haalbaar is, of mij
> > naar de juiste collega kunnen verwijzen? Met het oog op het naderende zomerreces hoor ik het
> > graag. Bij voorbaat dank.
> >
> > Met vriendelijke groet, [naam]
> >
> > _(Drenthe: "Provinciale Staten" eventueel vervangen door "het Drents Parlement".)_

**Unlocks (if done):** Flevoland (config-only — zero extra code for us). **Drenthe already unlocked.**
**Why:** Both run GemeenteOplossingen and expose the GO `/api/v2` (structure). We assumed the
**stemgedrag** votes weren't published because `/Samenstelling/{fractie}/votings` 404'd — but **Drenthe
proved that was a path issue, not a missing module**: its votes live at `/Leden/{fractie}/votings`. So
for Flevoland, the ask is really "please have GO confirm the votings path / enable the data." Utrecht
(`/Samenstelling/...`) and now Drenthe (`/Leden/...`) are both clear precedents.

**To:** Flevoland → `griffie@flevoland.nl` · Drenthe → `Statengriffie@drentsparlement.nl`
(✔ verified 2026-06-11. NB: the obvious guesses `statengriffie@flevoland.nl` and
`statengriffie@drenthe.nl` both **bounce** — Flevoland's griffie mailbox is `griffie@…` and
Drenthe brands its PS as the *Drents Parlement*, so its griffie lives on `@drentsparlement.nl`.)
**Onderwerp:** Verzoek: stemgedrag per fractie als open data publiceren (zoals provincie Utrecht)

> Geachte Statengriffie,
>
> Provincie Utrecht publiceert via haar stateninformatiesysteem (GemeenteOplossingen) het
> **stemgedrag per fractie** als open data — per motie/amendement is zichtbaar welke fractie voor
> of tegen stemde. Bij uw provincie is de GemeenteOplossingen-API wel beschikbaar, maar de
> **'stemgedrag'-module** lijkt niet ingeschakeld, waardoor de stemmingen niet als open data
> beschikbaar zijn.
>
> Zou u de stemgedrag-module kunnen (laten) inschakelen, of de stemmingen anderszins als open
> data willen publiceren? Ik bouw een open, non-commercieel overzicht van het stemgedrag in de
> Provinciale Staten en zou uw provincie daar graag aan toevoegen.
>
> Het project is open en non-commercieel; u kunt het hier bekijken:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
> (Provincie Utrecht, Noord-Holland en Limburg zijn er al in opgenomen — zo ziet het resultaat eruit.)
>
> Met vriendelijke groet,
> [naam]

> **Tip:** stuur aparte mails (Flevoland → `griffie@flevoland.nl`, Drenthe →
> `Statengriffie@drentsparlement.nl` — beide geverifieerd 2026-06-11). Vul je eigen naam in bij
> `[naam]`. De live links + de drie reeds opgenomen provincies zijn het overtuigendst — ze laten
> zien dat het een echt, werkend project is. (Voor Drenthe kun je "Provinciale Staten" in de mail
> eventueel vervangen door "het Drents Parlement".)

---

## 3. Publish-as-data lobby — Groningen & Zeeland  (Noord-Brabant ✅ resolved)

> **Basis (probed live 2026-07-05/06):** these publish who voted how, but only as **unstructured PDF**,
> not machine-readable open data:
> - **Groningen** (Notubiz) — votings API empty *and* portal render has no per-fractie markup (stemgedrag
>   module off; re-probed 2026-07-06), but the **Handelingen** name both sides per fractie + totals.
> - **Zeeland** (iBabs) — Stemming/Moties/Amendementen reports all 0 rows incl. the `Stemmen` field
>   (re-probed 2026-07-06 — genuinely empty), but the **concept-besluitenlijst** PDF names the voting fracties.
>
> So the ask is the same as §2: *publish the per-fractie vote you already record as open data.* Each has a
> **precedent on its own vendor** — cite it.
>
> **✅ Noord-Brabant is resolved — no lobby needed.** The mail was sent 2026-07-05, but the griffie (Emma
> Beers) replied 2026-07-06 that the votes are *already* in the portal behind "toon stemmen". They were
> right: NB is iBabs like Limburg, and its item detail carries the structured **`Stemmen`** field
> (per-fractie member counts) — we'd mis-filed it as notulen-only. **Shipped 2026-07-06 as tier A,
> config-only (628 items).** See §3c below and provinces.md. *(A short thank-you reply is warranted — see
> the draft at the end of §3c.)*
>
> **⏳ NUDGED 2026-11-06 — both, first time.** Neither had been chased since July (sent just before the
> zomerreces). What changed:
> - **Zeeland** now has **two** same-vendor precedents instead of one: Limburg *and* Noord-Brabant both
>   expose per-fractie counts in the iBabs **`Stemmen`** field, and NB's turned out to be populated
>   already. The nudge asks only whether that field can be filled for Zeeland.
> - **Groningen's original ask is partly obsolete and the nudge says so.** The July mail argued "bij andere
>   Notubiz-provincies kan ik het stemgedrag automatisch inlezen" — **no longer true since the portal block
>   (§6)**. Enabling their module alone would now achieve nothing, because the portal that carries the
>   per-fractie breakdown sits behind the same Cloudflare check. So the nudge asks for **both**: enable the
>   module *and* tell NotuBiz they do not object to automated retrieval (`/roles`), i.e. the §7 ask. It also
>   mentions that the same question is now with the four other Notubiz provinces — deliberate: five
>   griffies on one supplier, and griffies talk to each other. One resolution becomes everyone's precedent.
>
> Originals: ✅ sent 2026-07-05 to `statengriffie@provinciegroningen.nl` ·
> `statengriffier@zeeland.nl` (note the *-griffier* form). Cold contacts right before the **zomerreces
> (~mid-July)** — expect little before September; **nudge late August** if silent (Drenthe playbook: mail →
> nudge → result). NB's outcome is a useful nudge point: for Zeeland especially, "please populate the
> `Stemmen` field like Noord-Brabant and Limburg do" is now a same-vendor, same-field precedent.

### 3a. Groningen (Notubiz)
**To:** `statengriffie@provinciegroningen.nl` (✅ **sent 2026-07-05** — address correct).
**Onderwerp:** Verzoek: stemgedrag per fractie als open data publiceren (Notubiz stemgedrag-module)

> Geachte Statengriffie,
>
> Ik bouw een open, non-commercieel overzicht van het stemgedrag in de Provinciale Staten, en zou
> provincie Groningen daar graag aan toevoegen.
>
> In de **Handelingen** van uw Statenvergaderingen staat per motie/amendement keurig vermeld welke
> fracties voor en tegen stemden, met de aantallen. Diezelfde gegevens zijn via uw
> vergaderportaal (Notubiz) echter **niet als open data** beschikbaar: de stemmingen-API levert voor
> Groningen geen resultaten, terwijl dat bij andere Notubiz-provincies (Zuid-Holland, Gelderland,
> Fryslân, Overijssel) wél het geval is — daar kan ik het stemgedrag automatisch inlezen.
>
> Zou u de **stemgedrag-/stemmingenmodule** in Notubiz kunnen (laten) inschakelen, zodat de stemmingen
> die u toch al vastlegt ook als open data beschikbaar komen? Voor u is het naar verwachting een
> kwestie van publiceren; het werk van registreren doet u immers al.
>
> Het project is open en non-commercieel; u kunt het hier bekijken:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
> (Utrecht, Drenthe, Noord-Holland, Limburg en vier Notubiz-provincies zijn er al in opgenomen.)
>
> Met vriendelijke groet,
> [naam]

### 3b. Zeeland (iBabs)
**To:** `statengriffier@zeeland.nl` (✅ **sent 2026-07-05**. NB: it's `statengriffie**r**@zeeland.nl`
— the *-griffier* form, not `statengriffie@…` which was the wrong guess.)
**Onderwerp:** Verzoek: stemgedrag per fractie als open data publiceren (iBabs stemmingenregister)

> Geachte Statengriffie,
>
> Ik bouw een open, non-commercieel overzicht van het stemgedrag in de Provinciale Staten, en zou
> provincie Zeeland daar graag aan toevoegen.
>
> In de **concept-besluitenlijst** van uw Statenvergaderingen staat per motie/amendement/voorstel
> vermeld welke fracties voor stemden (bijvoorbeeld: *"aangenomen met de stemmen van de aanwezige leden
> van de fracties van BBB, CDA, CU, D66, PvdA-GL, PVV, SGP en VVD voor"*). Via uw vergaderportaal
> (iBabs) is dit stemgedrag echter **niet als open data** beschikbaar: de registers Moties,
> Amendementen en **Stemming** zijn leeg. Bij provincie Limburg — dat hetzelfde iBabs-systeem gebruikt —
> is het stemgedrag per fractie wél als open data ontsloten, en kan ik het automatisch inlezen.
>
> Zou u het **stemmingenregister** kunnen (laten) vullen / het stemgedrag per fractie als open data
> willen publiceren? De gegevens legt u in de besluitenlijst immers al vast; het gaat om het ook als
> data beschikbaar stellen.
>
> Het project is open en non-commercieel; u kunt het hier bekijken:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
> (Utrecht, Drenthe, Noord-Holland en Limburg zijn er al in opgenomen — zo ziet het resultaat eruit.)
>
> Met vriendelijke groet,
> [naam]

### 3c. Noord-Brabant (iBabs) — ✅ RESOLVED, no lobby needed

**Outcome (2026-07-06):** the lobby mail (sent 2026-07-05 to `statengriffie@brabant.nl`) got a reply from
the Statengriffie (**Emma Beers**): *"Op ons Stateninformatiesysteem zijn de hoofdelijke stemmingen
inzichtelijk … Door bij de stemuitslag te klikken op 'toon stemmen' zijn de stemmen van afzonderlijke
Statenleden in te zien."* She was right. NB is iBabs like Limburg, and the motie/amendement **item detail**
(not the report row) carries the structured **`Stemmen`** field — `vote-summary-legend-in-favour/-against`
with per-fractie member counts, exactly what the Limburg parser already reads. Our earlier "notulen-only"
verdict was a false negative: the *report row* and the `Stemverhouding` field are empty, but the `Stemmen`
field (behind "toon stemmen") is fully populated.

**Shipped 2026-07-06, config-only:** SOURCES entry (`vendor: ibabs`, `votes: stemmen`, Moties report
`376cf779-…` + Amendementen `0b5f0bd5-…`) → **628 stemmingen (534 moties + 94 amendementen), 15 fracties,
tier A** (per-member counts, incl. verworpen). One data fix: NB records the combined CU-SGP fractie as
`ChristenUnie/SGP` until 2025 and `ChristenUnie-SGP` from 2026 — merged via an alias.

**Lesson:** on iBabs, check **both** vote fields on the item detail — `Stemverhouding` (free text, NH) *and*
`Stemmen` (structured, Limburg/NB) — not just the report row. This is worth re-checking on any future iBabs
province before concluding "no structured votes".

> **Thank-you reply to Emma Beers — ✅ sent 2026-07-06** (reply on the same thread). Graceful close: confirmed
> the tip worked and that NB is now included — which also quietly reinforces the "publish as data" point for Zeeland.
>
> > Geachte mevrouw Beers,
> >
> > Hartelijk dank voor uw reactie en de tip. U heeft gelijk — via "toon stemmen" bij de stemuitslag zijn
> > de stemmen per Statenlid inderdaad in te zien, en het blijkt dat die per fractie ook als gestructureerde
> > data in het portaal beschikbaar zijn. Ik heb provincie Noord-Brabant daarmee inmiddels aan het overzicht
> > kunnen toevoegen: het stemgedrag per fractie op alle moties en amendementen van deze Statenperiode wordt
> > nu automatisch ingelezen.
> >
> > U kunt het resultaat hier bekijken: https://carefulcamel61097.github.io/wie-stemde-wat/
> >
> > Nogmaals dank voor het meedenken.
> >
> > Met vriendelijke groet,
> > [naam]

> **Note (superseded):** the old fallback plan — parse the verbatim notulen (member-name roll-call) and map
> member → fractie via NB's **Ledenlijst PS** report — is no longer needed now that the `Stemmen` field
> gives the same tier A directly. Kept for reference only.

---

## 4. Statengriffie Utrecht — votings-route achter een anti-bot-scherm (Anubis)
> **✅ RESOLVED 2026-09-05 — fastest turnaround yet (≈1 day).** Mailed 2026-09-04 19:44; Meike Kievits
> (Informatieadviseur, Statengriffie PS Utrecht) replied 21:23 the next evening: GemeenteOplossingen
> deployed a "botstopper" this summer against cyberattacks, which also caught legitimate interest.
> Four minutes later, a second mail: **the vendor had already added an exception for our User-Agent.**
> Verified the same evening — `/Samenstelling/{fractie}/votings` returns JSON again, Utrecht recollected
> to 610 stemmingen, `known_issue` marker removed.
>
> She also noted **no stemmingen have taken place since 9 July**; the next Statenvergadering is
> **30 September 2026**. That independently confirms the dataset was never incomplete — 610 items both
> before and after the outage — only unable to refresh.
>
> **What worked (reuse this):** name the exact URL, state what still works (`/api/v2/*`), offer two
> concrete fixes rather than a problem, and quantify the load (≈80 requests/week). The griffie
> forwarded it to the vendor essentially verbatim. Naming the **User-Agent string** in the mail is what
> made the exception a copy-paste job.

**Unlocks:** restores **Utrecht** (610 stemmingen, tier A, exact per-member counts).
**Why:** `GET /Samenstelling/{fractie}/votings` used to return the per-fractie stemgedrag as JSON.
Since ~mid-July 2026 it answers HTTP 200 with an **Anubis 1.25.0** proof-of-work interstitial
(`<script id="anubis_version">"1.25.0"</script>`) instead. The `/api/v2/*` endpoints are **not**
behind it (`/api/v2/groups` and `/api/v2/meetings` still return JSON), but there is no
`/api/v2/votings` route — probed 2026-09-04, it 400s as an unknown resource. So the votes exist only
behind the wall. Anubis is a blanket anti-AI-crawler measure; open-data reuse is collateral, which is
what makes the ask small.

**To:** `statengriffie@provincie-utrecht.nl` (✅ **correct** — no bounce, replied within a day. Unlike
Flevoland/Drenthe, the `statengriffie@` form *is* right for Utrecht.)
**Onderwerp:** Stemgedrag Stateninformatie niet meer als open data op te halen

> Beste Statengriffie,
>
> Ik beheer een open, non-commercieel overzicht van het stemgedrag **per fractie** in de
> Provinciale Staten. Provincie Utrecht was daarin vanaf het begin de eerste provincie: dankzij de
> open data van Stateninformatie staan de Utrechtse stemmingen erin met exacte aantallen per fractie.
>
> Sinds half juli lukt het ophalen van die gegevens niet meer. De pagina
> `https://www.stateninformatie.provincie-utrecht.nl/Samenstelling/{fractie}/votings`
> gaf altijd JSON terug met het stemgedrag, maar levert nu een anti-bot-controlescherm (Anubis) in
> plaats van de data. De endpoints onder `/api/v2/` (bijvoorbeeld `/api/v2/groups` en
> `/api/v2/meetings`) werken wél gewoon — alleen de votings-route zit achter dat scherm.
>
> Ik ga ervan uit dat die maatregel bedoeld is tegen AI-crawlers die websites overbelasten, en niet
> tegen hergebruik van open data. Mijn verzoek is dan ook klein; zou één van deze twee kunnen:
>
> 1. de user-agent van mijn collector uitzonderen in het Anubis-beleid:
>    `wie-stemde-wat collector (open-data overview; contact via GitHub)`
> 2. óf het stemgedrag ook via `/api/v2/` beschikbaar maken — dat deel staat immers niet achter het scherm.
>
> Het gaat om weinig verkeer: één keer per week ongeveer tachtig verzoeken in totaal, netjes
> gespreid. Dat is minder belasting dan één gemiddelde bezoeker.
>
> Het project is open en non-commercieel; u kunt het hier bekijken:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
>
> Wellicht ten overvloede: het gaat om dezelfde software (GemeenteOplossingen) als bij het Drents
> Parlement. Daar bleek een vergelijkbare vraag met één instelling bij de leverancier opgelost;
> mogelijk is dat hier ook zo.
>
> Op dit moment toont de site de Utrechtse gegevens nog wel, maar met de stand van 9 juli 2026 — die
> loopt dus steeds verder achter. Ik hoor graag of dit mogelijk is.
>
> Met vriendelijke groet,
> [naam]

> **Tip:** de concrete URL plus "de `/api/v2/`-endpoints werken wél" is het nuttigste deel van de
> mail — daarmee kan de griffie het één-op-één doorzetten naar GemeenteOplossingen zonder zelf te
> hoeven uitzoeken wat er stuk is. Vul je eigen naam in bij `[naam]`.

---

## 5. Notubiz — openbare API niet bereikbaar vanuit cloudomgeving (CI)
> **✅ ANSWERED — closed (reply received by 2026-09-15).** Maarten Lierop (NotuBiz Nederland B.V., Product
> owner Bestuurlijke Besluitvorming & Security): requests can be blocked for several reasons, including the
> sending servers' location, or IP addresses blacklisted after earlier suspicious traffic "by you or others".
> His first guess is the **GEO-IP block**: **"Hierop maken wij geen uitzonderingen. U kunt de requests dan
> wel uitvoeren van Nederlandse servers."**
>
> **Checked the same day:** his guess is only partly right. From the maintainer's home connection in
> **Thailand** (3BB, AS45758, no VPN or proxy) both `api.notubiz.nl` (HTTP 200) and the portal (HTTP 200)
> work. So it is not "Netherlands only"; it blocks some countries (the US runners), datacenter networks,
> or both. We did not tell Notubiz that; it would only invite a tighter rule.
>
> **Outcome:** no exception is possible, so the four provinces are refreshed weekly **from the home
> PC** by a Windows scheduled task (`collector/refresh-notubiz.ps1`; see coverage.md § Status van de
> bronnen). Fallback if the PC is off too often: a small **Dutch** server, which Notubiz itself
> suggested. Test a datacenter IP first (hourly billing), because of the blacklist remark.

**Unlocks:** automatic weekly refresh for **Zuid-Holland, Fryslân, Gelderland, Overijssel**. The data is
already live, but it only refreshes via a manual local run.
**Why:** diagnosed 2026-09-13 from two GitHub runners (Azure eastus 20.83.175.21, westus 52.159.245.146).
DNS and a control host are fine, but **TCP to `api.notubiz.nl:443` (195.20.144.5) times out**. That is a
silent firewall drop before any HTTP happens, so **a User-Agent exception (the Utrecht fix, §4) cannot
work here**. The Cloudflare-fronted portal `pzh.notubiz.nl` returns **HTTP 403**. Every run from the
maintainer's own connection in **Thailand** succeeded, so a geo-block outside NL/EU is unlikely. Filtering
of cloud/datacenter traffic fits the evidence better. So the mail *asks* about their policy rather than
proposing a fix.

**To:** Notubiz (same contact as §1, `info@notubiz.nl`)
**Onderwerp:** Openbare API niet bereikbaar vanuit cloudomgeving (open-data hergebruik)

> Beste Notubiz,
>
> In juni heb ik contact met u gehad over een API-token voor open stemdata van de Provinciale Staten.
> Dank nogmaals voor uw reactie. Een token bleek uiteindelijk niet nodig: via de openbare API en het
> publieksportaal kon ik het stemgedrag per fractie voor **Zuid-Holland, Fryslân, Gelderland en
> Overijssel** opnemen in een open, non-commercieel overzicht:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
>
> Ik loop nu tegen één probleem aan. De gegevens worden wekelijks automatisch ververst via GitHub
> Actions, dat draait op cloudservers van Microsoft Azure. Vanaf die servers zijn uw systemen niet
> bereikbaar:
>
> - `api.notubiz.nl` (195.20.144.5): de verbinding op poort 443 krijgt geen antwoord en loopt na
>   10 seconden in een time-out. DNS en andere websites werken daar wel.
> - `pzh.notubiz.nl`: geeft een HTTP 403.
>
> Vanaf een gewone internetverbinding werken precies dezelfde verzoeken zonder problemen. Ik neem aan dat
> dit een beveiligingsmaatregel is tegen verkeer uit datacenters en niet specifiek bedoeld tegen hergebruik
> van openbare gegevens. Daarom twee vragen:
>
> 1. Klopt het dat verkeer vanuit cloudomgevingen bewust wordt tegengehouden?
> 2. Is er een manier waarop uw openbare API en portaal automatisch vanuit zo'n omgeving gebruikt kunnen
>    worden? Bijvoorbeeld via een uitzondering, een aanbevolen route of voorwaarden waaraan ik me moet
>    houden.
>
> Het gaat om beperkt verkeer: één keer per week circa 350 verzoeken in totaal, met pauzes ertussen. Ik kan
> dat desgewenst verder terugbrengen tot alleen nieuwe vergaderingen. De collector identificeert zich met
> de user-agent `wie-stemde-wat collector (open-data overview; contact via GitHub)`.
>
> Alvast hartelijk dank voor het meedenken.
>
> Met vriendelijke groet,
> Thabiso Epema

> **If they offer "only new meetings":** `notubiz_events` currently re-pages the whole term every week.
> Limiting `date_from` to the last few weeks and merging into the existing JSON would cut it to a few
> dozen requests. The 350 figure = ~12 events pages + (41+45+43+37 meetings) × 2.

---

## 6. Notubiz — publieksportaal blokkeert nu ook het ophalen (Cloudflare 403)
> **✅ Sent 2026-11-06**, as a reply on the §5 thread to **Maarten Lierop** (Product owner Bestuurlijke
> Besluitvorming & Security) — same person who answered within hours in September. Subject amended to
> *Publieksportaal blokkeert nu ook het ophalen van stemmingen*.
> **Follow-up:** if silent by **~20 November** (≈2 weeks), nudge. **Hard deadline: around 22 November**
> the four provinces pass `STALE_AFTER_DAYS` (45, counted from the last good run on 2026-10-08) and the
> weekly CI run starts failing every week.
>
> _Nudge draft (reply on the same thread):_
> > Beste Maarten,
> >
> > Op 6 november stuurde ik onderstaande vraag over het Cloudflare-controlescherm op de
> > publieksportalen, waardoor het stemgedrag per fractie niet meer op te halen is. Zou u kunnen laten
> > weten of één van de twee genoemde opties mogelijk is, of mij naar de juiste persoon kunnen
> > verwijzen? Alvast dank!
> >
> > Met vriendelijke groet, Thabiso Epema

**Blocks:** **Zuid-Holland, Fryslân, Gelderland, Overijssel** — frozen at **2026-10-08**. The site shows
the "niet ververst" notice on all four (past `NOTICE_AFTER_DAYS`).
**Why:** since early October the public portals answer **HTTP 403 with a Cloudflare "Just a moment..."
challenge** — `pzh.notubiz.nl`, `fryslan.notubiz.nl` and the rest, from an ordinary non-datacenter
connection that worked fine before (verified 2026-11-06). `api.notubiz.nl` itself still returns 200, but
it keys votes by `role_id` and the `role_id → fractie` map sits behind the auth-walled `/roles` endpoint
— exactly what was refused in §1. Portal + API together are what made this tier A, so per-fractie data
is currently unobtainable. **We do not attempt to solve the challenge**: that is circumventing an access
control, and open asking is what has actually worked on this project (§2, §3c, §4).

**The ask (two options, either is fine):**
1. An exception for the collector's user-agent on the public portals.
2. Or access to `/roles`, so the portal is not needed at all — **framed as the lighter route for their
   servers**, which is true: API-only drops every portal page fetch.

**To:** reply on the §5 thread → Maarten Lierop / `info@notubiz.nl`
**Onderwerp:** Publieksportaal blokkeert nu ook het ophalen van stemmingen

> Beste Maarten,
>
> In september liet u weten dat verzoeken vanuit cloudomgevingen worden tegengehouden door de
> GEO-IP-blokkade, en dat ik de verzoeken wel vanaf een gewone (niet-datacenter) verbinding kon
> uitvoeren. Dat heb ik sindsdien gedaan, en dat werkte goed: de stemmingen van Zuid-Holland, Fryslân,
> Gelderland en Overijssel werden wekelijks bijgewerkt.
>
> Sinds begin oktober lukt dat niet meer. De publieksportalen geven nu een Cloudflare-controlescherm
> met een HTTP 403:
>
> - `https://pzh.notubiz.nl/vergadering/...` → 403 ("Just a moment...")
> - `https://fryslan.notubiz.nl/` → 403, idem
>
> Dit geldt voor alle provincies die ik gebruik, en ook vanaf dezelfde gewone verbinding die eerder
> prima werkte. Ik wil dat controlescherm uiteraard niet omzeilen, dus leg ik de vraag bij u neer.
>
> Het probleem is de combinatie van twee dingen:
>
> 1. `api.notubiz.nl` werkt nog wel, maar geeft de stemmen per `role_id`. De koppeling
>    `role_id → fractie` zit achter het `/roles`-endpoint, dat authenticatie vereist — precies wat in
>    juni niet verstrekt kon worden.
> 2. Het portaal bevatte die fractienamen en aantallen wél, en is nu niet meer geautomatiseerd te
>    benaderen.
>
> Daarmee is het stemgedrag **per fractie** op dit moment niet meer op te halen, terwijl het op het
> portaal voor bezoekers gewoon openbaar is. Ik neem aan dat dat niet de bedoeling is van de maatregel.
>
> Zou één van deze twee mogelijk zijn?
>
> 1. Een uitzondering voor mijn collector op de publieksportalen. Die identificeert zich met de
>    user-agent `wie-stemde-wat collector (open-data overview; contact via GitHub)`.
> 2. Of toegang tot `/roles` (de koppeling `role_id → fractie`), zodat ik het portaal niet meer nodig
>    heb en alleen de API gebruik. Dat is voor uw servers ook de lichtste route.
>
> Het gaat om weinig verkeer: één keer per week, netjes gespreid, en ik kan dat desgewenst beperken tot
> alleen nieuwe vergaderingen.
>
> Het project is open en non-commercieel:
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
>
> Alvast dank voor het meedenken.
>
> Met vriendelijke groet,
> Thabiso Epema

> **Fallback if Notubiz says no (not mentioned in the mail — keep it as a second step):** the four
> **provinces** own this data, and their griffies can ask Notubiz on our behalf. Griffies have been the
> more responsive route throughout (§2 Drenthe, §3c Noord-Brabant, §4 Utrecht). Addresses would need
> verifying first.

---

## 7. Statengriffies van de 4 Notubiz-provincies — toestemming voor geautomatiseerd ophalen
> **✅ Sent 2026-11-06** to all four. Notubiz refused an exception (§6) but **referred us here**, which is
> the whole basis of this ask — their words are quoted verbatim in the mail so the griffie does not have to
> take our word for it: *"Toegang tot het afgeschermde deel van de API, zoals /roles, geven wij alleen in
> opdracht van of in overleg met onze klanten. De provincies zijn eigenaar van deze gegevens. Daarom is de
> Statengriffie van de betreffende provincie het juiste aanspreekpunt."*
> **Follow-up:** nudge **~20 November** if silent. CI starts failing weekly ~2026-11-22 (45-day ceiling).
> Four parallel threads: one reply is enough to unblock that province.
>
> **⏳ GELDERLAND — engaged, same day.** The griffie's **informatiemanager** replied within 25 minutes:
> request and both routes are clear, she is taking it up internally **and with NotuBiz**. Her one open
> question: **what are the security risks of the two options?** She expects them to be small but wants it
> checked. She also noted Gelderland is currently up to date (correct — our newest vote is 2026-09-23) and
> that their next Statenvergadering is **woensdag 11 november**, which she does not expect to beat.
> (Direct contact details are in the private notes, not here.)
>
> **Answered 2026-11-06** with a written risk comparison. The line that matters: **option 1 (`/roles`) is
> the safer one and we said so ourselves** — read-only, exposes only the already-public `role_id → fractie`
> mapping, scopeable to one organisation, revocable, credential kept out of the public repo, and it
> *lowers* load (~90 portal requests/week → a handful of API calls). **Option 2 (UA exception) is weaker
> and we said that too**: a user-agent is self-declared and spoofable, so an exception on it genuinely
> loosens their protection, and it keeps the heavier portal traffic. IP allowlisting was offered as the
> stronger variant but ruled out honestly (no fixed IP). Closed with: we are not trying to circumvent the
> check, which is why we are asking — the sentence that has to survive being forwarded to NotuBiz security.
>
> **Lesson forming:** when a griffie asks about risk, naming the weakness of your own preferred ask buys
> more credibility than reassurance does. Same pattern as the Utrecht mail (§4): give them something they
> can forward verbatim.

**Blocks:** **Zuid-Holland, Fryslân, Gelderland, Overijssel** — frozen at 2026-10-08 (see §6).
**The ask:** have Notubiz grant either (1) access to the shielded `/roles` endpoint — pitched as the
**lighter** route for Notubiz, which is true: API-only drops every portal fetch — or (2) a user-agent
exception on the public portal.

**Addresses** (each from an official source, 2026-11-06). NB: **Gelderland is `griffie@`, not
`statengriffie@`** — the kind of detail that bounced Flevoland and Drenthe guesses in June:

| Provincie | Adres | Bron |
|---|---|---|
| Zuid-Holland | `statengriffie@pzh.nl` | officielebekendmakingen.nl (prb-2023-3279) |
| Fryslân | `statengriffie@fryslan.frl` | fryslan.frl/gast-van-de-staten |
| Gelderland | `griffie@gelderland.nl` | gelderland.nl/themas/politiek/ps/statengriffie |
| Overijssel | `statengriffie@overijssel.nl` | organisaties.overheid.nl/16790 |

**Onderwerp:** Stemgedrag Provinciale Staten niet meer als open data beschikbaar — verzoek aan Notubiz

> Geachte Statengriffie,
>
> Ik beheer een open, non-commercieel overzicht van het stemgedrag per fractie in de Provinciale Staten.
> Provincie [NAAM] is daarin opgenomen sinds juni: op elke motie en elk amendement is te zien hoe elke
> fractie stemde, met exacte aantallen, op basis van de gegevens in uw eigen vergaderportaal.
>
> – Website: https://carefulcamel61097.github.io/wie-stemde-wat/
> – Broncode: https://github.com/carefulCamel61097/wie-stemde-wat
>
> Sinds begin oktober kan ik die gegevens niet meer bijwerken. Het publieksportaal van Notubiz geeft nu
> een beveiligingscontrole (Cloudflare, HTTP 403) bij geautomatiseerd ophalen. Voor bezoekers is het
> stemgedrag nog gewoon zichtbaar; alleen hergebruik als data is niet meer mogelijk.
>
> Ik heb dit bij Notubiz neergelegd. Zij lieten weten dat het een bewuste maatregel is waarop zij geen
> uitzonderingen maken, en verwezen mij door naar u. Hun antwoord was duidelijk over de route:
>
> > "Toegang tot het afgeschermde deel van de API, zoals /roles, geven wij alleen in opdracht van of in
> > overleg met onze klanten. De provincies zijn eigenaar van deze gegevens. Daarom is de Statengriffie
> > van de betreffende provincie het juiste aanspreekpunt."
>
> Mijn verzoek is dus: zou u bij Notubiz kunnen aangeven dat u er geen bezwaar tegen heeft dat deze
> gegevens geautomatiseerd opgehaald worden? Concreet gaat het om één van beide:
>
> 1. Toegang tot het afgeschermde API-onderdeel `/roles`, dat de koppeling tussen een stem en de fractie
>    bevat. Met die toegang heb ik het portaal niet meer nodig en gebruik ik alleen de API — voor Notubiz
>    de lichtste route.
> 2. Of een uitzondering voor mijn collector op het publieksportaal.
>
> Het gaat om weinig verkeer: één keer per week, netjes gespreid, en desgewenst beperkt tot alleen nieuwe
> vergaderingen.
>
> Notubiz wees mij ook op Open Raadsinformatie. Dat heb ik nagekeken: die dataset bevat voor de provincies
> wel vergaderingen, agendapunten en documenten, maar geen stemmingen per fractie. Het stemgedrag staat
> daar alleen in de PDF's. Het is dus geen alternatief.
>
> Alvast hartelijk dank voor het meedenken.
>
> Met vriendelijke groet,
> Thabiso Epema

> **ORI checked, 2026-11-06 (so this claim is safe to make):** `api.openraadsinformatie.nl/v1/elastic` is
> genuinely open and provinces live in `osi_*` indices — but only **five** (Fryslân, Limburg,
> Noord-Holland, Overijssel, Utrecht; **not** Zuid-Holland or Gelderland), and across **every** `osi_*`
> index the only @types are MediaObject / AgendaItem / Meeting / Person / Report / Organization /
> Membership / ImageObject. **No VoteEvent, no Vote, and no vote-, stem-, result- or count-field in the
> mapping.** Votes exist there only inside the PDFs — the same wall as Groningen and Zeeland.

