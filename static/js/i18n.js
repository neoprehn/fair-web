/* DE/EN-Beschriftungs-Umschalter (rein clientseitig, localStorage - bewusst GETRENNT von
 * Djangos translation/gettext und der WaehrungLocaleMiddleware, die nur das Zahlenformat
 * steuert: Sprache und Zahlenformat sollen unabhängig voneinander wählbar sein).
 *
 * Als externe Datei statt Inline-Script, damit die (deutschen UND englischen) Beschriftungen
 * nicht im HTML-Response jeder Seite als Text auftauchen - sonst würden z.B. berechtigungs-
 * abhängig ausgeblendete Aktionswörter wie "Bearbeiten" trotzdem im Seitenquelltext stehen
 * (verwirrend und bricht naive Text-Assertions wie in tests/test_berechtigungen.py).
 */
window.FAIR_I18N = window.FAIR_I18N || { de: {}, en: {} };
Object.assign(window.FAIR_I18N.de, {
    nav_start: "Start", nav_szenarien: "Szenarien", nav_vergleiche: "Vergleiche",
    menu_label: "Menü", menu_hilfe: "Hilfe & Bedienung", menu_appkonfig: "App-Konfiguration",
    menu_angreifertypen: "Angreifertypen", menu_admin: "Admin-Bereich",
    menu_angemeldet_als: "Angemeldet als", menu_ki_einstellungen: "KI-Einstellungen",
    menu_abmelden: "Abmelden",
    footer_claim: "FAIR Monte Carlo mit PyFair", footer_doku: "Dokumentation",
    btn_bearbeiten: "Bearbeiten", btn_loeschen: "Löschen", btn_speichern: "Speichern",
    btn_abbrechen: "Abbrechen", btn_vorschau: "Vorschau",
    feld_name: "Name", feld_beschreibung: "Beschreibung", feld_verteilung: "Verteilung",
    feld_parameter: "Parameter", feld_unsicherheit: "Unsicherheit",
    feld_annahmen: "Annahmen", feld_quellentext: "Quellentext",
    det_fair_faktoren: "FAIR-Faktoren", det_risikotoleranz: "Risikotoleranz",
    det_konstante_schwelle: "Konstante Schwelle", det_schliessen: "Schließen",
});
Object.assign(window.FAIR_I18N.en, {
    nav_start: "Home", nav_szenarien: "Scenarios", nav_vergleiche: "Comparisons",
    menu_label: "Menu", menu_hilfe: "Help & Usage", menu_appkonfig: "App Configuration",
    menu_angreifertypen: "Threat Actor Types", menu_admin: "Admin Area",
    menu_angemeldet_als: "Signed in as", menu_ki_einstellungen: "AI Settings",
    menu_abmelden: "Sign out",
    footer_claim: "FAIR Monte Carlo with PyFair", footer_doku: "Documentation",
    btn_bearbeiten: "Edit", btn_loeschen: "Delete", btn_speichern: "Save",
    btn_abbrechen: "Cancel", btn_vorschau: "Preview",
    feld_name: "Name", feld_beschreibung: "Description", feld_verteilung: "Distribution",
    feld_parameter: "Parameters", feld_unsicherheit: "Uncertainty",
    feld_annahmen: "Assumptions", feld_quellentext: "Source text",
    det_fair_faktoren: "FAIR factors", det_risikotoleranz: "Risk tolerance",
    det_konstante_schwelle: "Constant threshold", det_schliessen: "Close",
});
(function () {
    function aktuelleSprache() {
        try { return localStorage.getItem('fairLang') === 'en' ? 'en' : 'de'; } catch (e) { return 'de'; }
    }
    // Für JS-generierten Text außerhalb von data-i18n (z.B. Plotly-Achsentitel/Legenden, die
    // beim Chart-Aufbau einmalig als String gebraucht werden statt als DOM-Attribut).
    window.fairT = function (key) {
        return (window.FAIR_I18N[aktuelleSprache()] || {})[key] || key;
    };
    function wendeAn() {
        var lang = aktuelleSprache();
        var dict = window.FAIR_I18N[lang] || {};
        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            var v = dict[el.getAttribute('data-i18n')];
            if (v !== undefined) el.textContent = v;
        });
        ['placeholder', 'title', 'aria-label'].forEach(function (attr) {
            document.querySelectorAll('[data-i18n-' + attr + ']').forEach(function (el) {
                var v = dict[el.getAttribute('data-i18n-' + attr)];
                if (v !== undefined) el.setAttribute(attr, v);
            });
        });
        document.documentElement.setAttribute('lang', lang);
        var btn = document.getElementById('lang-toggle');
        if (btn) { var l = btn.querySelector('.lang-label'); if (l) l.textContent = lang === 'de' ? 'EN' : 'DE'; }
    }
    window.fairApplyLang = wendeAn;
    var btn = document.getElementById('lang-toggle');
    if (btn) btn.addEventListener('click', function () {
        try { localStorage.setItem('fairLang', aktuelleSprache() === 'de' ? 'en' : 'de'); } catch (e) {}
        wendeAn();
    });
})();
