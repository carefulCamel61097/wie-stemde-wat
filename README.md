# Wie stemde wat?

**▶ Live: https://carefulcamel61097.github.io/wie-stemde-wat/**

> Ik wil zien wie wat gestemd heeft in de provinciale staten.

Een overzicht van het **stemgedrag per partij** op moties, amendementen en besluiten in de
Provinciale Staten. Per stemming zie je in één tabel of elke fractie **Voor (V, groen)** of
**Tegen (T, rood)** was — gebaseerd op open data van de provincie zelf.

**v1: alleen provincie Utrecht, huidige periode (2023–2027).** De interface heeft al een
provinciekiezer; andere provincies volgen in v2 (zie [roadmap.md](roadmap.md)).

## Hoe het werkt

```
collector (Python)  ->  data/utrecht.json  ->  statische site  ->  GitHub Pages
        ^                                                              ^
        └──────────  GitHub Actions (wekelijks) ververst de data  ─────┘
```

- **Geen server, geen database.** De data is een gegenereerd JSON-bestand dat de site inleest.
- De `collector/` haalt de stemmingen op uit het GemeenteOplossingen-platform achter
  `stateninformatie.provincie-utrecht.nl`, maakt de **unie** van alle stemmingen (een
  afwezige partij ontbreekt in haar eigen lijst) en schrijft een genormaliseerde dataset.
- De ruwe aantallen (`voor` / `tegen` / `onthouden`) staan in de data; V/T wordt in de
  browser afgeleid (`voor > tegen`). Zo blijven afsplitsingen en uitzonderingen zichtbaar.

Technische details en de teruggevonden endpoints: [data-sources.md](data-sources.md).

## Lokaal draaien

```bash
python collector/collect.py      # ververs data/utrecht.json (alleen stdlib, geen install)
python -m http.server 8000       # bekijk de site op http://localhost:8000
```
> De site moet via een server bekeken worden (niet `index.html` dubbelklikken): browsers
> blokkeren `fetch` van het databestand bij openen via `file://`.

## Documentatie
- [context.md](context.md) — doel, visie en scope
- [roadmap.md](roadmap.md) — stappen, beslissingen en toekomstplannen
- [data-sources.md](data-sources.md) — databron, API-endpoints en datamodel

## Bron & licentie
Data: **open data van Provincie Utrecht / Statengriffie**
(`https://www.stateninformatie.provincie-utrecht.nl`). Dit project hergebruikt die data en
is geen officiële uitgave van de provincie.
