# fair-web Dokumentation

**fair-web** schätzt Informationsrisiken nach dem **FAIR**-Modell (Factor
Analysis of Information Risk) als **erwarteten Jahresschaden** – per
Monte-Carlo-Simulation. Rechen-Engine ist der erweiterte **pyfair**-Fork
([neoprehn/pyfair](https://github.com/neoprehn/pyfair)).

Live-App: <https://fair.neoprehn.de>

## Was diese Doku abdeckt

Diese Seite dokumentiert **beides**: die Bedienung der Web-App **und** die
darunterliegende Python-Engine (den pyfair-Fork) – auf dem Detailgrad der
[Original-pyfair-Doku](https://pyfair.readthedocs.io/en/latest/), aber an den
erweiterten Funktionsumfang des Forks angepasst.

### FAIR-Grundlagen

- **[FAIR-Taxonomie](fair-taxonomie.md)** – die Risikofaktoren und ihre
  Ableitung (angelehnt an Open FAIR / O-RT).

### pyfair (Engine)

- **[Installation](installation.md)** – Einbindung des Forks.
- **[Schnellstart](schnellstart.md)** – ein vollständiges Beispiel in wenigen
  Zeilen.
- **[Modelle erstellen](modelle.md)** – die `FairModel`-API.
- **[Eingaben & Verteilungen](eingaben.md)** – Legacy- und strukturierte
  Eingabe-API, alle Verteilungen, Konfidenz-Mapping.
- **[Meta-Modelle](metamodelle.md)** – mehrere Modelle summieren (`sum`) oder
  vergleichen (`compare`).
- **[Berichte](berichte.md)** – HTML/CSV-Reports erzeugen.
- **[Serialisierung & Datenbank](serialisierung.md)** – Modelle als JSON
  speichern/laden, SQLite-Ablage.
- **[Fork-Erweiterungen](pyfair-fork.md)** – was der Fork gegenüber dem
  Original zusätzlich kann.

### Web-App

- **[Bedienung (fair-web)](bedienung.md)** – wie die Web-App benutzt wird.

!!! note "Status"
    Die Engine-Kapitel beschreiben den **neoprehn-Fork** von pyfair. Eine
    vollständige zweisprachige (DE/EN) Fassung ist in Arbeit; maßgebliche
    Referenz bei Unklarheiten ist der
    [Quellcode des Forks](https://github.com/neoprehn/pyfair).
