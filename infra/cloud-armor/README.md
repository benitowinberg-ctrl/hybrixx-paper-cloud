# HYBRIXX – Cloud Armor Firewall-Vorlage (noch NICHT aktiviert)

Die Terraform-Datei `main.tf` **erstellt nur eine Cloud-Armor-Sicherheitsrichtlinie**. Sie schützt **nichts**, bis die Richtlinie einem echten Load-Balancer-Backend zugewiesen wurde. Sie ist **nicht** für die öffentliche GitHub-Pages-Seite nutzbar.

## Voraussetzungen für späteren Echtgeldbetrieb

1. Eigenes verifiziertes Google-Cloud-Projekt mit bestätigter Abrechnung, Kostenbudget und Administratorkonto mit Passkey/2FA.
2. **Privater** Cloud-Run-Dienst mit `ingress=internal-and-cloud-load-balancing` und **IAM/IAP Authentisierung**; niemals `allUsers`-Invoker für Admin oder Handelsendpunkte.
3. External Application Load Balancer mit Serverless NEG für den privaten Dienst und HTTPS-Zertifikat.
4. Cloud Armor Policy über `terraform init`, `terraform plan` und ausschließlich nach Kosten- und Sicherheitsprüfung `terraform apply -var=project_id=PROJECT_ID` anlegen. **Die Policy ist ohne Backend-Anbindung wirkungslos.**
5. Policy dem vorgesehenen Backend Service zuweisen, verifizieren, dass der Cloud-Run-Standard-Endpunkt nicht direkt öffentlich erreichbar ist, und IAP/Cloud-Run-IAM-Zugriff für nicht authentifizierte Nutzer ablehnt.
6. WAF-Signaturen sind zunächst **preview = true**, d. h. sie protokollieren, blockieren aber noch nicht. Nach Log-Analyse und Tests vorsichtig auf `false` setzen. Die Rate-Begrenzung blockiert oberhalb von 60 Anfragen/Minute pro IP mit HTTP 429.
7. Testen: anonyme Zugriffe, falsche Identität, Replay, große Last, kaputte Marktdaten, doppelte Orders, fehlgeschlagene Transfers und Secret-Lecks müssen zuverlässig und getrennt fehlschlagen.
8. Cloud Logging/Monitoring und **unabhängige externe Alarmierung** aktivieren. Bei einem kompromittierten GitHub-Konto darf dessen Sicherheits-Issue nicht die einzige Warnung bleiben.

**Kostenhinweis:** Google Cloud Armor, Load Balancer, Logging und Dienste können Kosten verursachen. Nicht automatisch deployen oder Rechnungen aktivieren. Die derzeitige GitHub-Paper-Engine verwendet keine dieser Ressourcen.

**Wichtig:** Der Cloud-Armor-Standard erlaubt verbleibende Requests; nur ein korrekt authentisierter und autorisierter privater Backend-Dienst schützt vor unerlaubten Handelsaktionen. Die WAF erkennt nicht jeden KI-Angriff oder Trojaner. Kein Geheimnis oder Börsenschlüssel darf in diesem öffentlichen Repository stehen.

Quellen:
- https://cloud.google.com/armor/docs/security-policy-overview
- https://cloud.google.com/armor/docs/configure-waf
- https://cloud.google.com/run/docs/securing/ingress
