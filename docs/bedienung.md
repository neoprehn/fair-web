# Bedienung (fair-web)

Diese Seite fasst die Bedienung der Web-App zusammen. In der App selbst findest
du dieselben Inhalte unter **Menü → Hilfe & Bedienung**.

## Szenario anlegen

Über **Szenarien → + Neues Szenario**:

- **Name / Beschreibung** – frei.
- **Anzahl Simulationen** – Monte-Carlo-Iterationen (mehr = genauer, langsamer;
  10.000 ist üblich).
- **Zufalls-Seed** – gleicher Seed → reproduzierbares Ergebnis.

## FAIR-Faktoren & der Baum

Risk = **Häufigkeit (LEF)** × **Schaden (LM)**. Du gibst einen *Schnitt* durch
den Baum ein: jeden Ast so weit herunterbrechen, bis du den Faktor schätzen
kannst. Klick auf einen Faktor faltet ihn in seine Teilfaktoren auf. Nur die
**Blätter deines Schnitts** musst du ausfüllen – pyfair rechnet nach oben bis
Risk. Pro Faktor gibt es ein optionales **Annahmen**-Freitextfeld.

## Verteilungen & Unsicherheit

Pro Faktor eine Verteilung (je Faktortyp eingeschränkt): **PERT**,
**Lognormal**, **Beta** (Wahrscheinlichkeiten), **Poisson** (Zähl-Häufigkeiten),
**Normal/Konstant**. Der **Unsicherheits-Schieber** (5 Stufen) steuert die
Streubreite; die Formparameter je Stufe sind im Admin konfigurierbar.

## Risikotoleranz

Optional – legt fest, welches Risiko akzeptabel ist (als rote Kurve über die LEC
mit Schnittpunkt): **Konstant** (Schwelle €), **Kurve** (Punkte) oder
**Verteilung** (z. B. Lognormal mit Mittelwert, sigma, Samples).

## Simulation & Ergebnis

Während der Eingabe zeigt die **Live-Vorschau (LEC)** schon eine Schätzung. Der
volle Lauf liefert: Mittelwert/Median/Worst-Case (P95), **VaR** (10–99 %), die
**LEC** (log-Achse), den **Schnittpunkt** mit der Risikotoleranz, Histogramme
(Verteilung & Häufigkeit) und eine **Knoten-Detailtabelle**.

## Cluster (Szenarien gruppieren)

Cluster sind **organisatorische Gruppen** (Ordner/Kategorien) – rein zur
Übersicht, **ohne eigene Berechnung**. Ein Szenario kann in mehreren Clustern
liegen.

- **+ Neuer Cluster** (Übersicht) – Name, Beschreibung und zugeordnete Szenarien
  wählen.
- Über der Szenario-Tabelle erscheint eine **Filterleiste**: ein Klick auf einen
  Cluster zeigt nur dessen Szenarien (**Alle** hebt den Filter auf).
- Zugeordnete Cluster stehen als **Badge** am Szenario (klickbar → filtert) und
  auf der Detailseite.

## Szenarien vergleichen

Eigener Reiter **„Vergleiche"** in der Navbar: listet alle Vergleiche mit dem
gespeicherten **Gesamtrisiko (Ø)** des letzten Laufs und Link zum Lauf.

- **+ Neuer Vergleich** – mehrere Szenarien gruppieren und gemeinsam berechnen.
- Im Ergebnis umschaltbar zwischen **Compare** (LECs überlagert) und **Add**
  (Gesamtrisiko-Summe).
- Optional ein **Referenz-Szenario**, dessen Risikotoleranz im Compare-Chart rot
  gezeichnet wird (mit Schnittpunkten je Szenario-LEC).

Technisch entspricht ein Vergleich einem pyfair-[Meta-Modell](metamodelle.md).

## Klonen & Kopien

- **Klonen** (Übersicht) – dupliziert ein Szenario unter neuer ID als „… (Kopie)".
- **Als neues Szenario speichern** (Bearbeiten) – legt den aktuellen Stand als
  neue Kopie an, Original bleibt unverändert.

## Rollen

**Betrachter** (nur ansehen) · **Analyst** (anlegen/bearbeiten/simulieren) ·
**Konfigurator** (+ App-Konfiguration & Angreifertypen) · **Administrator**
(alles inkl. Benutzerverwaltung).
