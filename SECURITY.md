# HYBRIXX – Sicherheitskonzept (Stand: 15.10.2026)

## Sicherheitsstatus – zuerst lesen
- **Aktuell:** GitHub-Repository, GitHub-Pages-Dashboard und `state.json` sind **öffentlich**. Es existiert **kein privater HYBRIXX-Login** und **keine Firewall für GitHub Pages**.
- **Paper-only:** `paper_v2.py` holt ausschließlich öffentliche XRP/EUR-Marktdaten ab, simuliert Trades und sendet **keine echten Orders**.
- **Keine Geheimnisse** im HTML, JSON, Repository, in GitHub Issues, im Sprachchat, in Actions-Logs oder in Commit-Verläufen speichern. Ein späteres Entfernen löscht sie nicht sicher aus der Git-Historie.
- Der automatisierte Geheimnis-Check in `security_check.py` ist nur ein Basisfilter und ersetzt keine vollständige Prüfung.

## Eigentümerprinzip
1. Primärer Eigentümer: Inhaber des GitHub-Kontos `benitowinberg-ctrl`. Die tatsächliche Identität muss durch den jeweiligen Login-Anbieter **kryptografisch authentifiziert** werden. Ein frei eingegebener Benutzername oder Sprachbefehl zählt **nicht** als Identitätsprüfung.
2. Admin-Login über GitHub bzw. künftig Google Cloud mit einem **eigenen, zufällig erzeugten Passwort** (mindestens 20 Zeichen), idealerweise Passkey plus Zwei-Faktor-Schutz. Zugangsdaten werden ausschließlich im Passwortmanager des Eigentümers erzeugt und gespeichert, niemals im Repository oder Chat.
3. Im Zukunftsbetrieb: eigenständiger **privater Admin-Dienst** in Google Cloud Run, `Require authentication` / **Identity-Aware Proxy (IAP)**, Zugriff ausschließlich auf die persönliche Google-Identität, standardmäßig kein anonymer Zugang. Keine selbstgeschriebene HTML-Passwortabfrage.
4. Zusätzlich für Trading: alle Aktionen serverseitig autorisieren, mit auditierbarem Nutzer- und Zeitnachweis und Anti-Replay-Schutz. Weder Frontend-Buttons noch Text-/Spracheingaben dürfen den Schutz umgehen.
5. Bei Echtgeldbetrieb: nur Spot, ohne Hebel, minimaler API-Schlüssel mit **Trade-Recht, aber ohne Withdrawal-Rechte**; Börsenkonto mit 2FA und separater Genehmigung aktivieren. Secret Manager statt Klartextdateien.
6. **Zwei Freigaben** vor LIVE: (a) Eigentümer authentifiziert sich stark über den Identitätsanbieter und (b) bestätigt den Live-Betrieb explizit über ein kontrolliertes Admin-UI mit Limits. Standardeinstellung **PAPER_ONLY**.
7. Auszahlungen/Profit-Vault: zunächst ausschließlich buchhalterische Buchung. Keine automatische Überweisung und keine API-Auszahlungsberechtigung.
8. **Not-Aus:** neuer Echtgeldhandel wird bei Datenfehlern, falscher Identität, Wiederholungsversuch, nicht bestätigtem Live-Modus und Limitverletzungen blockiert. Offene Börsenpositionen müssen eigenständig sicher behandelt werden.
9. Protokollierung, Rate-Limit, Alarmierung und WAF/Netzwerkfilter ergänzen, sobald der **private Backend-Dienst** existiert. Cloud-Run-IAP schützt nicht das öffentliche GitHub-Pages-Dashboard.
10. **Sprechbefehle sind Bedienungswünsche, kein Sicherheitsnachweis.** Keine gesprochenen PINs oder Passwörter; echte Echtgeld-/Sicherheitsaktionen benötigen eine separate, geschützte Bestätigung.

## Sofort beim GitHub-Konto
- [GitHub Password and authentication](https://github.com/settings/security): einzigartiges starkes Passwort in einem Passwortmanager und Passkey/2FA prüfen.
- [GitHub Installed Applications](https://github.com/settings/installations): unbekannte Apps und Berechtigungen überprüfen.
- [GitHub Security](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/security): Repository-Hinweise prüfen.
- Kein Binance-, Kraken- oder Google-API-Schlüssel in öffentliche Repositories einfügen.

## Bevor Echtgeld auch nur testweise erlaubt wird
- Privaten Cloud-Run-Dienst mit IAP deployen; nur dem Eigentümer Zugriff gewähren und nicht authentifizierte Anfragen testen.
- Echte Order-APIs und kritische Kontrollfunktionen ausschließlich in den authentifizierten privaten Backend-Dienst verlagern.
- Abgeschottete Secrets und private Datenbank einrichten; keinerlei Trading-Zugangsdaten in GitHub Pages.
- Berechtigungen, TOTP/Passkey, Rate-Limits, Sperrverhalten, Orderduplikate, Kill-Switch und Verlustlimits nachweislich testen.
- Separate menschliche Freigabe vor Aktivierung von Echtgeld. Ohne diese Schritte bleiben alle Börsenaufträge deaktiviert.

**Achtung:** Diese Datei ist ein Sicherheitsplan und die Code-Checks sind eine erste Schutzmaßnahme. Sie erstellen **noch keinen geschützten HYBRIXX-Login**. GitHub Pages kann kein sicheres, nur im HTML eingebautes Passwort erzwingen.


## Security Sentinel v1 – automatische Erkennung und Warnung
- Workflow: [Security Sentinel](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/actions/workflows/security-sentinel.yml), geplant alle vier Stunden sowie bei Änderungen auf main. GitHub kann Zeitpläne verzögern oder auslassen.
- Überprüft öffentlich eingecheckte Zugangsdaten, eine kleine Liste von riskanten Ausführungsfunktionen und nicht genehmigten URL-Konstanten in den Paper-Handelsdateien, sowie auffällige Änderungen am **öffentlichen** Paper-Zustand (Zeiten, Coin-Symbol, Guthaben, Trade-Felder).
- **Fail closed:** Die Paper-Automatik prüft die Schutzregeln unmittelbar vor dem Start. Bei Fund wird der betroffene Lauf gestoppt. Ein gesonderter Warn-Workflow erstellt oder aktualisiert ein [GitHub Issue](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/issues) bei fehlgeschlagener Sentinel-Prüfung. Das Issue ist **öffentlich**, deshalb stehen dort keine Geheimnisse.
- Der Warnmechanismus über GitHub Issues benötigt **Issues aktiviert** und die Schreibberechtigung des GitHub-Actions-Tokens; wenn das fehlt, bleibt der fehlgeschlagene Workflow im Actions-Protokoll sichtbar.
- Warnungen an dein Handy/E-Mail hängen von den [GitHub-Benachrichtigungseinstellungen](https://github.com/settings/notifications) ab. Eine Push/SMS-Garantie existiert nicht.
- Diese Signatur-/Schema-Prüfungen erkennen **nicht jeden Trojaner, unbemerkte Kontoübernahmen oder raffinierte Supply-Chain-/KI-Angriffe**. Es gibt **noch keine Netz-Firewall, keine Laufzeit-Verhaltensanalyse und keine echte Intrusion-Detection**. Wer den GitHub-Account mit Schreibrechten kontrolliert, könnte auch die Prüfungen ändern.
- KI-/Prompt-Injection-Schutz: Informationen aus Kurs-APIs, Webseiten, Mails, Chats oder KI-Ausgaben sind stets **unvertrauenswürdige Daten**. Sie dürfen niemals als Programmcode oder Autorisierungsbefehl interpretiert oder ausgeführt werden; Handelsausführung benötigt eigene, serverseitige Freigaben.

## Zusätzliche GitHub-Schutzfunktionen, die der Kontoinhaber einschalten muss
1. In [Repository Advanced Security](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/settings/security_analysis) **CodeQL Default Setup**, Secret Scanning und Push Protection einschalten, sofern die entsprechenden Schalter angeboten werden. Das ist eine zusätzliche Prüfung, nicht durch Sentinel ersetzt.
2. Unter [Rules / Branch Protection](https://github.com/benitowinberg-ctrl/hybrixx-paper-cloud/settings/rules) \`main\` schützen: Pull Request und erfolgreiche Sicherheitschecks verlangen, unkontrollierte Force Pushes verbieten. Dabei muss der bereits vorhandene geplante GitHub-Actions-Schreibzugriff auf \`state.json\` berücksichtigt werden; ein strikter Branch-Schutz würde dessen automatisches Committen zunächst blockieren. Deshalb ist eine private Datenbank statt Git-Commits das Ziel.
3. [GitHub Benachrichtigungen](https://github.com/settings/notifications) für Actions-Fehler und neue Issues prüfen.
4. Vor Echtgeld: separater Server mit starker Identitätsprüfung, geschützt gespeicherten Schlüsseln, Netzwerkfilter, Anmelde-/Orderprotokollen und unabhängiger Alarmierung; diese Schutzfunktionen sind **noch nicht aktiv**.
