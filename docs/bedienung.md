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
Risk. Pro Faktor gibt es ein optionales **Annahmen**-Freitextfeld (zusätzlich
ein **Quellentext**-Feld für Belege/Zitate).

Verzweigungsknoten (**TEF**/**Vulnerability** auf der Häufigkeits-, **PL**/**SL**
auf der Schadensseite) sind im Baum und in den Tabellen farblich markiert –
dieselbe Farbe taucht konsistent überall auf, wo der jeweilige Zweig
vorkommt. Im Ergebnis-Baum werden nur tatsächlich **verwendete Knoten**
gezeigt (die deines Schnitts); nicht genutzte Teilfaktoren bleiben ausgeblendet.

## Loss-Magnitude-Aufschlüsselung (6 Forms of Loss / FAIR-MAM)

Primary Loss (PL) und Secondary Loss (SL) lassen sich statt als ein direkter
Wert auch **feiner aufschlüsseln** – umschaltbar über **Loss-Magnitude-Eingabe**
im Szenario-Formular:

- **Klassisch** – PL/SL je ein direkter Wert im Baum (Standard, unverändert).
- **6 Forms of Loss** – PL und SL je Seite in bis zu sechs klassische
  Verlustarten zerlegen (Productivity, Response, Replacement, Competitive
  Advantage, Fines & Judgements, Reputation), als zwei Reiter dargestellt. Nur
  ausgefüllte Formen zählen; sie werden **elementweise pro Simulations-Trial**
  zu PL/SL aufsummiert (nicht nur deren Kennwerte).
- **FAIR-MAM-Fragebogen** – feinere Aufschlüsselung nach den 10
  FAIR-MAM-Kostenmodulen (26 Kategorien, als aufklappbare Module), bei denen
  Primary/Secondary (→ PL/SL) je Kategorie fest vorgegeben ist. Verweist auf
  FAIR-MAM™ (FAIR Institute, nicht-kommerzielle Nutzung).

Zwei zusätzliche Umschalter erscheinen, sobald eine Aufschlüsselung aktiv ist:

- **Aggregationsmodus** – *Elementweise* faltet die Formen/Kategorien exakt
  per Monte-Carlo (Standard); *Kennwerte* addiert nur Mittelwert+Varianz und
  nähert die Summe über eine Lognormalverteilung an (schneller, ungenauer in
  der Form).
- **SLEF-Modus** (nur Secondary Loss) – *Gemeinsam* nutzt den SLEF-Knoten im
  Baum als einen Multiplikator auf die gesamte SL-Summe (SL im Baum auf
  „aufschlüsseln" stellen, dort SLEF eintragen); *Individuell* gibt jeder
  SL-Form/-Kategorie eine eigene SLEF-Verteilung.

## KI-Unterstützung (optional)

Neben der Beschreibung und jedem Annahmen-Feld kann ein **✨-Button**
einen KI-Vorschlag einholen – siehe [KI-Agent](ki-agent.md) für
Konfiguration (eigenes Modell pro Nutzer) und Bedienung.

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
(Verteilung & Häufigkeit), ein **Streudiagramm Primär-/Sekundärverlust** (ein
Punkt je simuliertem Jahr: x = PL, y = SL – zeigt den Zusammenhang zwischen
beiden) und eine **Knoten-Detailtabelle**.

## C/I/A-Kennzeichnung

Im Szenario-Formular als Mehrfachauswahl: welche Schutzziele
(**Confidentiality**/**Integrity**/**Availability**) das Szenario betrifft –
ein Szenario kann mehrere gleichzeitig betreffen. Erscheint als Badge auf der
Detail- und der Ergebnisseite.

## Cluster (Szenarien gruppieren)

Cluster sind **organisatorische Gruppen** (Ordner/Kategorien) – rein zur
Übersicht, **ohne eigene Berechnung**. Ein Szenario kann in mehreren Clustern
liegen. Die Zuordnung erfolgt **ausschließlich auf der Cluster-Seite selbst**
(nicht im Szenario-Formular).

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
- Im Ergebnis umschaltbar zwischen **Compare** und **Add** – der Schalter steuert
  nicht nur die LEC-Kurve, sondern die ganze Seite: **Compare** zeigt die
  Szenarien einzeln (LECs überlagert, Beitrag- und Schnittpunkt-Tabelle je
  Zeile); **Add** zeigt ausschließlich das Gesamtrisiko (Summenkurve, Gesamt-
  Kennzahlen-Karten, Summenzeile in beiden Tabellen).
- Optional ein **Referenz-Szenario**, dessen Risikotoleranz im Compare-Chart rot
  gezeichnet wird (mit Schnittpunkten je Szenario-LEC).

Technisch entspricht ein Vergleich einem pyfair-[Meta-Modell](metamodelle.md).

## Klonen & Kopien

- **Klonen** (Übersicht) – dupliziert ein Szenario unter neuer ID als „… (Kopie)".
- **Als neues Szenario speichern** (Bearbeiten) – legt den aktuellen Stand als
  neue Kopie an, Original bleibt unverändert.

## Anzeige: Hell/Dunkel & Sprache

Oben rechts in der Navigation zwei Umschalter (pro Browser gemerkt, kein
Neuladen nötig): **Hell/Dunkel** fürs Farbschema und **DE/EN** für die festen
Beschriftungen (Navigation, Formularlabels, Diagrammtitel). Der
Sprachumschalter ist unabhängig vom Zahlenformat, das weiterhin an die global
konfigurierte Währung gekoppelt ist (€ → 1.234,56, $ → 1,234.56). Aktuell
abgedeckt: Startseite, Szenario-Übersicht/-Formular/-Detail, Ergebnisseite.
Nutzereingaben (Szenario-Namen, Beschreibungen, Annahmen) werden dabei nicht
übersetzt – dafür ist eine eigene Funktion in Vorbereitung (siehe unten).

## Rollen

**Betrachter** (nur ansehen) · **Analyst** (anlegen/bearbeiten/simulieren) ·
**Konfigurator** (+ App-Konfiguration & Angreifertypen) · **Administrator**
(alles inkl. Benutzerverwaltung).

Für eine künftige automatische Übersetzung von Szenario-Inhalten (Name,
Beschreibung, Annahmen) kann der Administrator bereits einen
**DeepL-API-Key** in der App-Konfiguration hinterlegen – die Übersetzungs-
funktion selbst ist noch nicht angebunden.
