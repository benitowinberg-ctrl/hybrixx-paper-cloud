# HYBRIXX Paper Cloud — kostenloser GitHub-Actions-Test

Diese **neue Minimalversion** ruft stündlich den XRP/EUR-Kurs bei Kraken ab und speichert ihn in `state.json`. Das virtuelle Startkapital beträgt 500 EUR. **Noch keine automatischen BUY/SELL-Trades**: erst die Datenversorgung prüfen, dann eine Strategie mit Risikoregeln testen. Kein Echtgeldhandel, keine API-Schlüssel.

## Einrichtung
1. Die drei Dateien bzw. Ordner aus diesem ZIP **entpacken** und den Inhalt (nicht die ZIP-Datei selbst) in das private GitHub-Repository hochladen: `Add file` → `Upload files` → Dateien inklusive `.github/workflows/paper.yml`.
2. Repository → `Settings` → `Actions` → `General`: Actions erlauben und unter `Workflow permissions` **Read and write permissions** wählen, falls verfügbar; speichern.
3. Repository → `Actions` → `HYBRIXX Paper Observation` → `Run workflow`.
4. Nach erfolgreichem Lauf `state.json` prüfen. Der Zeitplan läuft ungefähr stündlich, kann aber verspätet sein oder ausfallen. Die Ausführung läuft unabhängig vom PC.

## Einschränkungen
- GitHub Actions ist **kein ununterbrochener 24/7-Prozess**. Der Workflow läuft nach Zeitplan, normalerweise stündlich.
- Bei privaten Repositories gelten GitHubs kostenlose Actions-Kontingente. Keine Kostenpflicht aktivieren.
- GitHub kann geplante Workflows bei längerer Inaktivität deaktivieren. Bei Konflikten mit parallelen Commits kann ein Lauf scheitern.
- Der Kursabruf erfordert Internetzugang zu Kraken; bei API-Fehlern schlägt der Lauf sichtbar fehl.
- Nicht als Finanzberatung oder Renditenachweis verwenden.
