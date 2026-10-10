# Usage (fair-web)

This page summarizes how to use the web app. Inside the app itself you'll
find the same content under **Menu → Help & Usage**.

## Creating a scenario

Via **Scenarios → + New Scenario**:

- **Name / Description** – free text.
- **Number of simulations** – Monte Carlo iterations (more = more accurate,
  slower; 10,000 is typical).
- **Random seed** – same seed → reproducible result.

## FAIR factors & the tree

Risk = **Frequency (LEF)** × **Loss (LM)**. You enter a *cut* through the
tree: break each branch down until you can estimate the factor. Clicking a
factor expands it into its sub-factors. You only need to fill in the
**leaves of your cut** – pyfair calculates upward to Risk. Each factor has
an optional free-text **Assumptions** field (plus a **Source text** field
for evidence/citations).

Branch nodes (**TEF**/**Vulnerability** on the frequency side, **PL**/**SL**
on the loss side) are color-coded in both the tree and the tables – the
same color appears consistently everywhere that branch occurs. The result
tree shows only the nodes actually **used** (those in your cut); unused
sub-factors stay hidden.

## Loss magnitude breakdown (6 Forms of Loss / FAIR-MAM)

Instead of a single direct value, Primary Loss (PL) and Secondary Loss (SL)
can also be **broken down in more detail** – switchable via
**Loss magnitude input** in the scenario form:

- **Classic** – PL/SL as one direct value each in the tree (default,
  unchanged).
- **6 Forms of Loss** – break PL and SL down per side into up to six
  classic loss types (Productivity, Response, Replacement, Competitive
  Advantage, Fines & Judgements, Reputation), shown as two tabs. Only
  filled-in forms count; they're summed **element-wise per simulation
  trial** into PL/SL (not just their summary statistics).
- **FAIR-MAM questionnaire** – a finer breakdown by the 10 FAIR-MAM cost
  modules (26 categories, as expandable modules), where Primary/Secondary
  (→ PL/SL) is fixed per category. References FAIR-MAM™ (FAIR Institute,
  non-commercial use).

Two additional toggles appear once a breakdown is active:

- **Aggregation mode** – *Element-wise* folds the forms/categories exactly
  via Monte Carlo (default); *Summary statistics* only adds mean+variance
  and approximates the sum via a lognormal distribution (faster, less
  accurate in shape).
- **SLEF mode** (Secondary Loss only) – *Shared* uses the SLEF node in the
  tree as a single multiplier on the total SL sum (set SL in the tree to
  "break down", enter SLEF there); *Individual* gives each SL form/category
  its own SLEF distribution.

## AI assistance (optional)

Next to the description and every assumptions field, a **✨ button** can
fetch an AI suggestion – see [AI Agent](ki-agent.md) for configuration
(each user's own model) and usage.

## Distributions & uncertainty

One distribution per factor (restricted by factor type): **PERT**,
**Lognormal**, **Beta** (probabilities), **Poisson** (count frequencies),
**Normal/Constant**. The **uncertainty slider** (5 levels) controls the
spread; the shape parameters per level are configurable in the admin.

## Risk tolerance

Optional – defines what risk is acceptable (drawn as a red curve over the
LEC with an intersection point): **Constant** (threshold in €), **Curve**
(points) or **Distribution** (e.g. lognormal with mean, sigma, samples).

## Simulation & results

While entering data, the **live preview (LEC)** already shows an estimate.
The full run delivers: mean/median/worst case (P95), **VaR** (10–99%), the
**LEC** (log axis), the **intersection point** with the risk tolerance,
histograms (distribution & frequency), a **primary/secondary loss scatter
plot** (one point per simulated year: x = PL, y = SL – shows the
relationship between the two) and a **node detail table**.

## C/I/A labeling

A multi-select in the scenario form: which protection goals
(**Confidentiality**/**Integrity**/**Availability**) the scenario affects –
a scenario can affect several at once. Shown as a badge on the detail and
result pages.

## Clusters (grouping scenarios)

Clusters are **organizational groups** (folders/categories) – purely for
overview, **with no calculation of their own**. A scenario can belong to
multiple clusters. Assignment happens **exclusively on the cluster page
itself** (not in the scenario form).

- **+ New Cluster** (overview) – choose a name, description and assigned
  scenarios.
- A **filter bar** appears above the scenario table: clicking a cluster
  shows only its scenarios (**All** clears the filter).
- Assigned clusters appear as a **badge** on the scenario (clickable →
  filters) and on the detail page.

## Comparing scenarios

A dedicated **"Compare"** tab in the navbar: lists all comparisons with the
stored **total risk (mean)** of the last run and a link to the run.

- **+ New Comparison** – group multiple scenarios and calculate them
  together.
- The result view toggles between **Compare** and **Add** – the switch
  controls not just the LEC curve but the whole page: **Compare** shows the
  scenarios individually (LECs overlaid, a row per scenario in the
  contribution and intersection tables); **Add** shows only the total risk
  (summed curve, total KPI cards, a sum row in both tables).
- Optionally a **reference scenario**, whose risk tolerance is drawn in red
  on the Compare chart (with intersection points per scenario LEC).

Technically, a comparison corresponds to a pyfair
[meta-model](metamodelle.md).

## Cloning & copies

- **Clone** (overview) – duplicates a scenario under a new ID as "… (Copy)".
- **Save as new scenario** (edit view) – saves the current state as a new
  copy, the original stays unchanged.

## Display: light/dark & language

Two toggles at the top right of the navigation (remembered per browser, no
reload needed): **Light/Dark** for the color scheme and **DE/EN** for the
fixed labels (navigation, form labels, chart titles). The language toggle
is independent of the number format, which remains tied to the globally
configured currency (€ → 1.234,56, $ → 1,234.56). Currently covered:
homepage, scenario overview/form/detail, result page. User-entered content
(scenario names, descriptions, assumptions) is not translated by this
toggle – a dedicated feature for that is in preparation (see below).

## Roles

**Viewer** (view only) · **Analyst** (create/edit/simulate) · **Configurator**
(+ app configuration & threat actor types) · **Administrator** (everything,
including user management).

For a future automatic translation of scenario content (name, description,
assumptions), administrators can already store a **DeepL API key** in the
app configuration – the translation feature itself is not yet wired up.
