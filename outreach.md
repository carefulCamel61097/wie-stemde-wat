# Outreach — draft e-mails to unlock more provinces

Two low-cost asks that could turn hard provinces into easy ones. See [provinces.md](provinces.md)
for why. Both are about **open data**, so there's good precedent (Utrecht already does this).

---

## 1. Notubiz — request an open-data API token
> **✅ Sent 2026-06-10.** Awaiting reply. If granted, build the Notubiz adapter (see roadmap NEXT).

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
**Unlocks (if done):** Flevoland, Drenthe (becomes config-only — zero extra code for us).
**Why:** Both run GemeenteOplossingen and expose the GO `/api/v2` (structure), but the optional
**stemgedrag** module isn't enabled, so per-party votes aren't published as open data (404 on
`/Samenstelling/{fractie}/votings`). Utrecht has it enabled — clear precedent.

**To:** statengriffie@flevoland.nl  /  statengriffie@drenthe.nl (verify addresses)
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
> Met vriendelijke groet,
> [naam]

---

## 3. (optional) Notubiz provinces with stemgedrag module off
Gelderland publicly shows only aangenomen/verworpen status (stemgedrag module off). The same
griffie ask as #2 could apply — but the Notubiz **token** (#1) is the more general unlock.
