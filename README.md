# HYBRIXX Paper Cloud — simuliertes XRP/EUR-Trading

**Nur virtuelles Geld.** Keine echten Börsenorders, kein Echtgeld, keine Handels-API-Schlüssel. Startsaldo **500 € virtuell**. Der öffentliche GitHub-Code speichert ausschließlich simulierte Kursmessungen und Trades.

## Automatischer Betrieb
- GitHub Actions ruft den XRP/EUR-Kurs über Krakens öffentliche Kurs-API ab.
- Die Engine `paper_v2.py` nutzt einen einfachen gleitenden-Durchschnitts-Vergleich (4/12 Beobachtungen) als **nicht validierte Teststrategie**.
- Sie simuliert maximal 25 % Paper-Kapital in XRP pro Position, Gebühren (angenommene 0,26 %) und Slippage (angenommene 0,10 %), 5 % Stop-Loss und 10 % Gewinnmitnahme.
- Ein 15-%-Drawdown des virtuellen Gesamtportfolios deaktiviert weitere Käufe (Safe Stop). Verkäufe zur Risikominderung bleiben möglich.
- Alle Kurse und simulierten Trades stehen im `state.json`. Der Zustand wird auf jedem Lauf fortgesetzt.
- Der Workflow `.github/workflows/paper.yml` führt zuerst Unit-Tests aus. Nur wenn alle Tests erfolgreich sind, wird die Paper-Engine ausgeführt.
- Automatischer Start auf `main` nach einem relevanten Code-Push, anschließend ungefähr stündlich (geplant Minute 17). GitHub-Zeitpläne sind nicht garantiert.
- Durch den Warm-up von 12 Kursbeobachtungen können **mehrere Stunden ohne Trade** vergehen. Kein Signal bedeutet nicht, dass die Engine ausgefallen ist.

## Bedienung
1. [Ergebnisse der GitHub Actions](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/actions) öffnen und den letzten Lauf **HYBRIXX Paper Trading (Simulation)** prüfen.
2. [Paper-Status](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/blob/main/state.json) zeigt Guthaben, letzten Kurs, Signal und virtuelle Trades.
3. [Dashboard](https://benitowinberg-ctrl.github.io/hybrixx-paper-cloud/) zeigt die in GitHub gespeicherten Daten. Es werden keine Live-Ticks versprochen.
4. Für einen einmaligen Lauf: GitHub → **Actions** → **HYBRIXX Paper Trading (Simulation)** → **Run workflow**.

## Entwicklung und Sicherheit
- Tests: `python -m unittest discover -s tests -v` (keine Zusatzpakete).
- Die Datei `paper.py` bleibt als historische Beobachtungsversion erhalten; aktiv ist `paper_v2.py`.
- Historische Kursdaten im Zustand werden **nicht zurückgesetzt**.
- Kursausfälle lassen den Workflow fehlschlagen statt stillschweigend Werte zu erfinden.
- Keine Sicherheit, dass die Strategie gewinnbringend ist. Für reales Trading sind unabhängige historische Tests, robuste Verlustlimits, API-Rechteverwaltung und eine andere zuverlässige Ausführungsumgebung nötig.
- GitHub Actions arbeitet in kurzen Läufen, **nicht als permanent laufender 24/7-Handelsprozess**.
