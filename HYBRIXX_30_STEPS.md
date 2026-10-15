# HYBRIXX — 30 sequenzielle Entwicklungsschritte (15.10.2026)

Status: **IMPLEMENTIERT** = Code im Repository, **OFFEN** = nicht als fertig behaupten.
Alle Erweiterungen bleiben Paper-only; kein Brokerage-Zugriff, keine API-Keys, keine Geldtransfers.

| Nr. | Maßnahme | Status | Akzeptanzkriterium |
|---:|---|---|---|
| 01 | Einheitliches virtuelles Kontobuch | IMPLEMENTIERT | Ein Ledger, keine doppelte Startsumme |
| 02 | 10 EUR-Kryptomärkte | IMPLEMENTIERT | Alle 10 Ticker werden geprüft |
| 03 | Marktpreis-Plausibilität | IMPLEMENTIERT | Ungültige Kurse stoppen Lauf |
| 04 | Transaktionsgebühren simulieren | IMPLEMENTIERT | Gebühren im Buch |
| 05 | Slippage simulieren | IMPLEMENTIERT | Fills berücksichtigen Abweichung |
| 06 | Maximal 3 Positionen | IMPLEMENTIERT | Limit im Simulator |
| 07 | Positionsgröße begrenzen | IMPLEMENTIERT | Höchstens 10 % je Position |
| 08 | Stop-Loss je Position | IMPLEMENTIERT | 5-%-Schwelle |
| 09 | Take-Profit je Position | IMPLEMENTIERT | 10-%-Schwelle |
| 10 | Drawdown-Schutz | IMPLEMENTIERT | 15-%-Safe-Stop |
| 11 | Notfallsperre respektieren | IMPLEMENTIERT | Keine Transaktionen bei Lock |
| 12 | Read-only Strategierecherche | IMPLEMENTIERT | Keine Kontoänderung |
| 13 | Chronologischer Trainings-/Testsplit | IMPLEMENTIERT | Holdout bleibt separat |
| 14 | Kauf-und-Halten-Vergleich | IMPLEMENTIERT | Benchmark im Report |
| 15 | Strategie-No-Trade-Gate | IMPLEMENTIERT | Negative Tests ablehnen |
| 16 | Menschlich inspirierte Risikoregeln | IMPLEMENTIERT | Vergleichsstrategien vorhanden |
| 17 | Cash-Alternative berücksichtigen | IMPLEMENTIERT | Null Trades möglich |
| 18 | Zwei Research-Gates kombinieren | IMPLEMENTIERT | Neue Käufe nur mit Doppel-Freigabe |
| 19 | Research-Frische prüfen | IMPLEMENTIERT | Abgelaufene Berichte blockieren |
| 20 | Bei fehlenden Daten fail-closed | IMPLEMENTIERT | Keine neue Kaufposition |
| 21 | Reproduzierbare Regressionstests | IMPLEMENTIERT | Tests im Workflow |
| 22 | Kontostand-Audit | IMPLEMENTIERT | Cash + Positionen = Equity |
| 23 | Maschinenlesbarer Risiko-/Reifebericht | IMPLEMENTIERT | Read-only Audit, 30 Prüfpunkte |
| 24 | Mehrjährige historische Kursdaten | OFFEN | Datenlizenz, Qualität, Vollständigkeit |
| 25 | Mehrere Marktregime | OFFEN | Bullen-, Bären- und Seitwärtsphasen |
| 26 | Rollierender Walk-forward-Test | OFFEN | Mehrere unberührte Holdouts |
| 27 | Monte-Carlo- und Bootstrap-Robustheit | OFFEN | Konfidenzintervalle dokumentiert |
| 28 | Portfolio-Korrelationen und Stressszenarien | OFFEN | Konzentrationsrisiko begrenzt |
| 29 | 24/7-Zuverlässigkeit mit Alarmierung | OFFEN | Laufzeit, Ausfälle, Benachrichtigungen gemessen |
| 30 | Separates Real-Trading-Sicherheitsreview | OFFEN | Nur nach ausdrücklicher Freigabe; kein Echtgeldbetrieb |

**Reihenfolge:** 23 verifizieren, danach 24–28 wissenschaftlich belastbar machen, 29 Betriebsnachweis, 30 separates Review. Kein Echtgeldhandel durch diese Roadmap autorisiert.
