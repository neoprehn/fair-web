# AI Agent (optional AI assistance)

fair-web can help draft text: for a scenario's **description** and for the
**assumptions** of each individual FAIR factor (LEF, TEF, CF, PoA,
Vulnerability, TC, CS, LM, PL, SL, SLEF, SLEM). The feature is **entirely
optional** – without configuration, input works as usual, with no AI
involved at all.

## Concept

- Every user brings their **own AI model**: provider, model name and API
  key are stored per user in the **AI settings**.
- The API key is stored **encrypted** in the database (Fernet, key derived
  from `SECRET_KEY`).
- Requests go **directly from the server** to the chosen provider
  (Anthropic, OpenAI or Google Gemini) – through the unified
  [`litellm`](https://github.com/BerriAI/litellm) interface.
- There is **no** centrally shared model – each user pays for and is
  responsible for their own API calls.

## Configuration (per user)

In the user menu (top right) → **"AI settings"**
(`/accounts/ki-einstellungen/`):

1. Choose a **provider**: Anthropic (Claude), OpenAI (GPT) or Google
   (Gemini).
2. **Model**: a free-text field with suggestions (datalist). This must
   contain the **exact model ID** from the provider's console/API docs
   (e.g. `claude-sonnet-4-5-20250929`, `gpt-4o`, `gemini-2.5-pro`) – the
   suggestions are only a starting point.
3. **API key**: paste and save. The field stays empty when reopened; a
   note indicates a key is already stored. **Leaving it empty** when
   saving = the existing key is left unchanged.

Model and provider can be changed at any time without re-entering the key –
just overwrite the field and save.

Without complete configuration (provider **and** model **and** API key), AI
assistance stays inactive; clicking an AI button then just shows a pointer
to the settings page.

## Usage in the scenario form

Next to the **description** and next to every **assumptions** field there's
a small **✨ button**. Clicking it opens an offcanvas panel:

1. In the "What should the AI do?" text field, a short instruction can be
   entered (optional – without text, the AI drafts a default suggestion).
2. **"Send request"** sends the current form state (name, description,
   distribution/parameters of the respective factor) together with the
   field-specific context to the configured model.
3. The response appears in the reply field; **"Apply"** writes it into the
   original field (with a confirmation prompt if it already contains text).

## Technical structure (for developers)

| Component | File | Purpose |
|---|---|---|
| Encryption | `apps/konten/krypto.py` | Fernet encryption of the API key |
| Per-user model | `apps/konten/models.py` (`KIEinstellung`) | Provider, model, encrypted key |
| Settings UI | `apps/konten/forms.py`, `views.py`, `templates/registration/ki_einstellungen.html` | GET/POST form |
| Prompt building blocks | `apps/szenarien/ki_prompts.py` | System prompts per field type |
| AI call | `apps/szenarien/ki_service.py` | `litellm.completion(...)`, error handling |
| AJAX endpoint | `apps/szenarien/views.py` (`ki_vorschlag`), `urls.py` | Accepts form state, returns `{"ok": ..., "antwort"/"fehler": ...}` |
| UI | `templates/szenarien/_node_fields.html`, `form.html` | ✨ buttons, offcanvas, JS |

### Prompt structure (`ki_prompts.py`)

Every request gets a **system prompt** that sets the role and context, plus
the user's free-form question as a "user" message (`ki_service.frage_ki`).

- **`prompt_beschreibung(szenario_name)`** – context: the scenario's name.
  Asks for a short (2–5 sentence) description, understandable to
  non-technical readers too, focused on the trigger, affected assets and
  potential loss.

- **`prompt_annahmen(code, szenario_name, szenario_beschreibung,
  verteilung, params)`** – context: the scenario's name/description as
  well as the factor's name, abbreviation and FAIR explanation (via
  `fair_tree.target(code)` / `abbr(code)` / `erklaerung(code)`), plus the
  currently configured distribution and parameters. Asks for a short (1–4
  sentence) justification of the chosen values.

### Factor-specific additional hints

So the AI considers the right FAIR concepts for certain factors, there's a
map `_ZUSATZ_HINWEISE` in `ki_prompts.py` (code → additional sentence
appended to the assumptions prompt). Currently defined:

- **LM, PL, SL, SLEM** – a reminder of the **six FAIR loss forms**
  (Productivity, Response, Replacement, Fines & Judgments, Competitive
  Advantage, Reputation); for SL/SLEM, additional focus on secondary
  stakeholders (authorities, customers, the public).
- **TC, CS** – framed as a **percentile** (of the actor or control-strength
  population).
- **CF, TEF** – justification via **industry-typical contact/attack rates**
  or threat intelligence data.
- **POA** – justification via the target's attractiveness and the
  effort/risk for the actor.
- **SLEF** – the share of primary events that trigger a reaction from
  secondary stakeholders.

#### Adding or adjusting hints

To refine the prompt for a factor, extend the map `_ZUSATZ_HINWEISE` in
`apps/szenarien/ki_prompts.py`, or adjust an existing entry:

```python
_ZUSATZ_HINWEISE = {
    "TC": "Frame the threat actor's capability as a percentile …",
    # add a further/adjusted hint for a code (e.g. "VULN"):
    "VULN": "…",
}
```

The hint is automatically appended to the respective factor's assumptions
prompt (`_hinweis(code)` in `prompt_annahmen`). For fundamental changes to
tone, language or length of the responses, `_BASIS` serves as the shared
building block for all prompts.

### Error handling & availability

`ki_service.ist_verfuegbar(user)` checks whether `KIEinstellung` is fully
configured (provider **and** model **and** API key).
`ki_service.frage_ki(...)` raises a `KIFehler` exception with a
user-friendly message if configuration is missing or the provider errors
out (e.g. an invalid key) – the `ki_vorschlag` endpoint returns this as
`{"ok": false, "fehler": "..."}` (never HTTP 500).

### Supported providers

Currently: **Anthropic (Claude)**, **OpenAI (GPT)**, **Google (Gemini)** –
via `litellm` with a provider prefix before the model name (e.g.
`anthropic/claude-sonnet-4-5-20250929`). Microsoft Copilot is deferred for
now (no open chat API available for third-party use), possibly retrofitted
later as an Azure OpenAI model.
