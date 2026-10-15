# Claude mit HYBRIXX verbinden

HYBRIXX nutzt die offizielle Anthropic Messages API. Die Verbindung ist
**ausschließlich ein unabhängiger Forschungs-Auditor** und hat keine Rechte,
Orders auszuführen, Konten zu ändern oder Modellgewichte zu installieren.

## Einrichtung

1. In der Anthropic Console unter https://console.anthropic.com/ einen API-Key
   erstellen. Ein Claude-Web-Abo ist nicht automatisch ein API-Guthaben.
2. In GitHub: Repository → Settings → Secrets and variables → Actions →
   **Secrets** → New repository secret. Name: `ANTHROPIC_API_KEY`.
   Den Key nur dort einfügen. **Nicht** in HTML, GitHub-Code oder Chat.
3. Unter **Variables** → New repository variable: `CLAUDE_MODEL`.
   Den genauen aktuellen Modellbezeichner aus der Anthropic Console verwenden.
   Es ist bewusst kein Modellname fest eingebaut.
4. Unter Actions den Workflow **HYBRIXX Claude Research Adviser (READ ONLY)**
   öffnen und **Run workflow** klicken.
5. Nach erfolgreichem Lauf das Artefakt `claude-research-advisory`
   herunterladen. Es enthält `claude_advisory_report.json`.

Der Workflow ist nur manuell startbar. Er hat `contents: read`, verwendet
GitHub Secrets und lädt das Ergebnis als kurzlebiges Actions-Artefakt hoch.
Es wird **nicht** in den öffentlichen Repository-Code committed. Achtung:
Bei einem öffentlichen Repository können Berechtigte je nach GitHub-
Konfiguration auf Actions-Artefakte zugreifen. Deshalb werden ausschließlich
öffentliche, aggregierte Forschungsmetriken an Claude gesendet.

## Sicherheit und Grenzen

- Es werden nur allowlist-basierte aggregierte Metriken übertragen.
- Die Anthropic API erhält diese Metriken zur Verarbeitung. Die aktuellen
  Anthropic-Datenschutz- und API-Bedingungen gelten.
- API-Aufrufe können Kosten verursachen.
- Fehlender Key, ungültige Daten und API-Fehler stoppen den Job.
- Claude-Ausgaben sind **unverbindliche Forschungskommentare**.
- Keine automatischen Code-Änderungen, Orders, Withdrawals oder Modellfreigaben.
- Die öffentliche GitHub-Pages-HTML enthält **keinen** API-Key.
- Ein Claude.ai-Chat-Abo allein kann nicht als API-Schlüssel verwendet werden.
