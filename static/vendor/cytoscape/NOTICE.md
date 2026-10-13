# cytoscape.js (vendored)

Version: 3.34.0
Quelle: https://www.npmjs.com/package/cytoscape
Lizenz: MIT (siehe `LICENSE`)

Lokal vendored statt per CDN geladen (wie im iam-Projekt, siehe dortiges
`frontend/vendor/cytoscape/NOTICE.md`) -- `cytoscape.min.js` 1:1 aus dem npm-Tarball kopiert,
keine Modifikation. Keine Laufzeit-Abhaengigkeiten (`dependencies: {}` im package.json), keine
Netzwerk-/Tracking-Aufrufe im Bundle (geprueft: kein `fetch`/`XMLHttpRequest`/`sendBeacon`).

Genutzt für die CAM-Kill-Chain-Grafik (`templates/cam/form.html`, `templates/cam/lauf.html`) --
interaktiver, draggable Graph statt statischem SVG, Kanten mit Labels, analog zum
Graph-Tab in `iam/frontend/analysis.html`.

Update: neue Version von https://registry.npmjs.org/cytoscape herunterladen, `dist/cytoscape.min.js`
ersetzen, Versionsnummer hier anpassen.
