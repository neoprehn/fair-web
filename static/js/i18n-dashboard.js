/* Seitenspezifisches DE/EN-Wörterbuch für templates/szenarien/dashboard.html - extern statt
 * inline, damit berechtigungsabhängig ausgeblendete Aktionswörter (z.B. "Neues Szenario",
 * "Bearbeiten") nicht trotzdem als Text im HTML-Response jeder Seite auftauchen (siehe
 * static/js/i18n.js für die ausführliche Begründung). */
Object.assign(window.FAIR_I18N.de, {
    dash_titel: "Szenarien", dash_neuer_cluster: "+ Neuer Cluster", dash_neues_szenario: "+ Neues Szenario",
    dash_cluster_label: "Cluster:", dash_alle: "Alle", dash_cluster_bearbeiten: "Cluster bearbeiten",
    dash_cluster_loeschen: "löschen", dash_gemeinsam_berechnen: "Ausgewählte gemeinsam berechnen",
    dash_th_simulationen: "Simulationen", dash_th_faktoren: "Faktoren", dash_th_geaendert: "Geändert",
    dash_th_aktionen: "Aktionen", dash_keine_faktoren: "Keine Faktoren",
    dash_cluster_badge_title: "Cluster", dash_klonen_title: "Als neues Szenario duplizieren",
    dash_btn_klonen: "Klonen", dash_leer: "Noch keine Szenarien angelegt.",
    dash_erstes_anlegen: "Erstes Szenario anlegen",
});
Object.assign(window.FAIR_I18N.en, {
    dash_titel: "Scenarios", dash_neuer_cluster: "+ New Cluster", dash_neues_szenario: "+ New Scenario",
    dash_cluster_label: "Cluster:", dash_alle: "All", dash_cluster_bearbeiten: "Edit cluster",
    dash_cluster_loeschen: "delete", dash_gemeinsam_berechnen: "Calculate selected together",
    dash_th_simulationen: "Simulations", dash_th_faktoren: "Factors", dash_th_geaendert: "Changed",
    dash_th_aktionen: "Actions", dash_keine_faktoren: "No factors",
    dash_cluster_badge_title: "Cluster", dash_klonen_title: "Duplicate as new scenario",
    dash_btn_klonen: "Clone", dash_leer: "No scenarios created yet.",
    dash_erstes_anlegen: "Create first scenario",
});
