# FAIR-Taxonomie

Die Faktoren angelehnt an die **Open-FAIR-Risikotaxonomie** (The Open Group,
O-RT). Die Ableitungen zeigen, wie sich jeder Faktor aus seinen Teilfaktoren
ergibt.

| Faktor | Bedeutung | Ableitung |
|---|---|---|
| **Risk** | Wahrscheinliche Häufigkeit *und* Höhe künftiger Verluste (Verteilung). | LEF × LM |
| **Loss Event Frequency (LEF)** | Häufigkeit, mit der ein Bedrohungsakteur tatsächlich Schaden zufügt. | TEF × Vulnerability |
| **Threat Event Frequency (TEF)** | Häufigkeit, mit der ein Akteur gegen ein Asset agiert. | CF × PoA |
| **Contact Frequency (CF)** | Häufigkeit, mit der ein Akteur mit dem Asset in Kontakt kommt. | – |
| **Probability of Action (PoA)** | Wahrscheinlichkeit, dass der Akteur nach Kontakt agiert (0–1). | – |
| **Vulnerability** | Wahrscheinlichkeit, dass ein Bedrohungsereignis zum Schaden wird. | TC vs. RS |
| **Threat Capability (TC)** | Fähigkeits-/Kraftniveau des Akteurs (0–1). | – |
| **Resistance Strength (RS)** | Stärke der Schutzmaßnahmen (in pyfair: Control Strength). | – |
| **Loss Magnitude (LM)** | Höhe des Verlusts je Ereignis. | PL + SL |
| **Primary Loss (PL)** | Direkter Verlust des primären Beteiligten (Asset-Eigner). | – |
| **Secondary Loss (SL)** | Verlust aus Reaktionen sekundärer Beteiligter. | SLEF × SLEM |
| **Secondary Loss Event Frequency (SLEF)** | Anteil der Primärereignisse mit Folgeschaden. | – |
| **Secondary Loss Event Magnitude (SLEM)** | Höhe des Sekundärverlusts je Ereignis. | – |

!!! tip "Interaktiv"
    In der App erklärt die **Startseite** jeden Faktor per Klick im FAIR-Baum –
    ganz ohne Simulation.
