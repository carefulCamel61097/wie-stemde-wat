# Wie stemde wat?

**▶ Live: https://carefulcamel61097.github.io/wie-stemde-wat/**

> Ik wil zien wie wat gestemd heeft in de provinciale staten.

Een overzicht van het **stemgedrag per partij** op moties, amendementen en besluiten in de
Provinciale Staten. Per stemming zie je in één tabel of elke fractie **Voor (V, groen)** of
**Tegen (T, rood)** was — gebaseerd op open data van de provincie zelf.

**Nu live: Utrecht, Noord-Holland en Limburg** (periode 2023–2027), via een provinciekiezer.
De collector is multi-province / multi-vendor (een adapter per platform):
- **Utrecht** (GemeenteOplossingen) — exacte aantallen per lid.
- **Limburg** (iBabs) — exacte aantallen per lid, inclusief *verworpen* moties/amendementen.
- **Noord-Holland** (iBabs) — alleen op fractieniveau (V/T), alleen aangenomen.

Hoe betrouwbaar elke bron is, staat per provincie in [coverage.md](coverage.md).

Naast de tabel: filters (type, partij, zoeken, uitslag, "alleen omstreden"), vastpinnen,
**CSV-download** van de selectie, en drie analyses (popups): **Overeenkomst** (overeenkomstmatrix
per partij), **Partijprofiel** en **Vergelijken** (twee partijen).

## Hoe het werkt

```
collector (Python)  ->  data/<provincie>.json  ->  statische site  ->  GitHub Pages
        ^                 (+ data/provinces.json)                          ^
        └──────────  GitHub Actions (wekelijks) ververst de data  ─────────┘
```

- **Geen server, geen database.** De data is een gegenereerd JSON-bestand dat de site inleest.
- De `collector/` heeft een **adapter per platform** (GemeenteOplossingen / iBabs; Notubiz volgt).
  Nu actief: Utrecht (GO) + Noord-Holland & Limburg (iBabs, twee stem-formaten). Hij normaliseert
  alles naar één schema en schrijft een dataset per provincie + een provincie-index.
- De aantallen (`voor` / `tegen` / `onthouden`) staan in de data; V/T wordt in de browser
  afgeleid (`voor > tegen`). Zo blijven afsplitsingen en uitzonderingen zichtbaar.

Technische details en de teruggevonden endpoints: [data-sources.md](data-sources.md).

## Lokaal draaien

```bash
python collector/collect.py      # ververs data/<provincie>.json (alleen stdlib, geen install)
python -m http.server 8000       # bekijk de site op http://localhost:8000
```
> De site moet via een server bekeken worden (niet `index.html` dubbelklikken): browsers
> blokkeren `fetch` van het databestand bij openen via `file://`.

## Documentatie
- [context.md](context.md) — doel, visie, scope en status
- [roadmap.md](roadmap.md) — stappen, beslissingen en de **▶ NEXT** (waar verder te gaan)
- [coverage.md](coverage.md) — wat we hébben per provincie + **betrouwbaarheid** per bron
- [data-sources.md](data-sources.md) — databron, API-endpoints (GO + iBabs + Notubiz) en datamodel
- [provinces.md](provinces.md) — alle 12 provincies: leverancier + haalbaarheid van stemdata
- [outreach.md](outreach.md) — concept-mails (Notubiz-token, griffies) om meer provincies te ontsluiten

## Bron & licentie
**Open data** van de provincies zelf (Provinciale Staten / Statengriffie): Utrecht
(GemeenteOplossingen), Noord-Holland en Limburg (iBabs publieksportaal). Dit project hergebruikt
die data en is geen officiële uitgave van de provincies.
