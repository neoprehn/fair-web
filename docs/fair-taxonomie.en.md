# FAIR Taxonomy

The factors follow the **Open FAIR risk taxonomy** (The Open Group, O-RT).
The derivations show how each factor results from its sub-factors.

| Factor | Meaning | Derivation |
|---|---|---|
| **Risk** | Probable frequency *and* magnitude of future loss (a distribution). | LEF × LM |
| **Loss Event Frequency (LEF)** | How often a threat actor actually inflicts loss. | TEF × Vulnerability |
| **Threat Event Frequency (TEF)** | How often an actor acts against an asset. | CF × PoA |
| **Contact Frequency (CF)** | How often an actor comes into contact with the asset. | – |
| **Probability of Action (PoA)** | Probability that the actor acts after contact (0–1). | – |
| **Vulnerability** | Probability that a threat event becomes a loss event. | TC vs. RS |
| **Threat Capability (TC)** | Skill/strength level of the actor (0–1). | – |
| **Resistance Strength (RS)** | Strength of the protective controls (in pyfair: Control Strength). | – |
| **Loss Magnitude (LM)** | Size of the loss per event. | PL + SL |
| **Primary Loss (PL)** | Direct loss to the primary stakeholder (asset owner). | – |
| **Secondary Loss (SL)** | Loss from secondary stakeholders' reactions. | SLEF × SLEM |
| **Secondary Loss Event Frequency (SLEF)** | Share of primary events that cause follow-on loss. | – |
| **Secondary Loss Event Magnitude (SLEM)** | Size of the secondary loss per event. | – |

!!! tip "Interactive"
    In the app, the **homepage** explains every factor by clicking through
    the FAIR tree – no simulation required.
