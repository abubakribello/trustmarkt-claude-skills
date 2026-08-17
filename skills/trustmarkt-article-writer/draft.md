Du hast DeepSeek getestet und warst beeindruckt. Die Antworten sind stark, das Tempo hoch, und im Vergleich zu ChatGPT oder Claude kostet es dich fast nichts. Der Gedanke liegt nahe: Warum nicht die ganze Firma damit arbeiten lassen? Genau an diesem Punkt lohnt sich ein kurzer Stopp.

Denn während du die Kosten pro Anfrage rechnest, rechnet jemand anderes mit: die Datenschutzbehörden. In Deutschland und Italien sind sie 2025 aktiv gegen DeepSeek vorgegangen – nicht wegen der Qualität der KI, sondern wegen dem, was im Hintergrund mit deinen Daten passiert.

Dieser Artikel macht den ehrlichen Check: Was die Behörden konkret unternommen haben, welche Daten DeepSeek wirklich sammelt, warum die DSGVO-konforme Nutzung so schwierig ist – und wie du die Stärke des Modells trotzdem nutzt, ohne die Daten deiner Kunden nach China zu schicken.

## Warum Behörden DeepSeek 2025 gestoppt haben

Der Reihe nach. Anfang 2025 ordnete die italienische Datenschutzbehörde Garante an, den Zugriff auf DeepSeek zu beschränken – zu unklar sei, wie und wo die Daten der Nutzer verarbeitet werden.

In Deutschland folgte der nächste Schlag am 27. Juni 2025: Die Berliner Beauftragte für Datenschutz meldete die DeepSeek-App bei Apple und Google als rechtswidrigen Inhalt und verlangte eine Prüfung zur Sperrung in den App-Stores. Die Begründung: DeepSeek überträgt personenbezogene Daten nach China, ohne die Voraussetzungen der DSGVO für einen solchen Drittlandtransfer zu erfüllen.

Zusätzlich warnt das Bundesamt für Sicherheit in der Informationstechnik (BSI), dass Tastatureingaben innerhalb der App potenziell schon vor dem Absenden mitgelesen werden können. Das ist keine Kleinigkeit: Aus dem Tippverhalten lassen sich Rückschlüsse auf Identität, Verhalten – im Zweifel sogar auf Passwörter – ziehen.

:::callout Wichtig zu verstehen
DeepSeek ist in Deutschland nicht pauschal "verboten". Aber wenn du es geschäftlich mit Kunden- oder Mitarbeiterdaten nutzt, bist du als Unternehmen verantwortlich – nicht der Anbieter. Und genau diese Nutzung sehen die Aufsichtsbehörden aktuell kritisch.
:::

## Was DeepSeek wirklich über dich und deine Kunden sammelt

Ein Blick in die Datenschutzangaben von DeepSeek zeigt, warum die Behörden nervös sind. Gesammelt und auf Servern in China gespeichert werden unter anderem:

- E-Mail-Adresse, Telefonnummer und Geburtsdatum aus der Registrierung
- Sämtliche Eingaben – also jeder Text und jede Audioaufnahme, die du hineingibst
- Der komplette Chatverlauf
- Technische Daten wie Gerätemodell, Betriebssystem und IP-Adresse
- Tastatureingabe-Muster und -Rhythmen

Das entscheidende Detail: Die Speicherung erfolgt auf Servern in China, ohne Opt-out. Nach chinesischer Rechtslage können staatliche Stellen auf diese Daten zugreifen. Sobald ein Mitarbeiter also einen Kundennamen, eine Vertragsklausel oder eine interne Kalkulation in DeepSeek eintippt, verlässt diese Information deinen Verantwortungsbereich – endgültig und unkontrollierbar.

## Das DSGVO-Problem in drei Punkten

Warum ist die Cloud-Version von DeepSeek für den Geschäftseinsatz so schwierig? Es sind drei Bausteine, die fehlen – und jeder einzelne reicht schon aus:

1. **Kein Angemessenheitsbeschluss.** Zwischen der EU und China gibt es keine Entscheidung, die ein vergleichbares Datenschutzniveau bestätigt. Jeder Datentransfer braucht deshalb zusätzliche Garantien, die DeepSeek nicht liefert.
2. **Kein Auftragsverarbeitungsvertrag (AVV).** Nach Art. 28 DSGVO brauchst du mit jedem Dienstleister, der für dich personenbezogene Daten verarbeitet, einen AVV. Für DeepSeek Cloud gibt es keinen.
3. **Kein EU-Vertreter.** Ein Anbieter aus einem Drittland muss nach Art. 27 DSGVO einen Vertreter in der EU benennen. Auch das fehlt.

Ohne diese Grundlage ist die geschäftliche Nutzung der Cloud-Version mit echten Personendaten praktisch nicht DSGVO-konform darstellbar.

## Cloud, Self-Hosted oder EU-Anbieter: der direkte Vergleich

Die gute Nachricht: "DeepSeek nutzen" ist keine reine Ja/Nein-Frage. Die Modelle R1 und V3 sind quelloffen (open-weight) – du kannst sie also auf eigener oder europäischer Infrastruktur betreiben. Dann verlässt kein einziges Byte deine Kontrolle.

| Variante | Wo liegen die Daten? | AVV / Drittland | Für Personendaten geeignet? |
| --- | --- | --- | --- |
| DeepSeek App/Cloud | Server in China | Kein AVV, kein EU-Vertreter | Nein |
| DeepSeek selbst gehostet (EU) | Deine/EU-Infrastruktur | Kein Transfer nötig | Ja, mit sauberem Setup |
| Etablierter EU-tauglicher Anbieter | EU-Rechenzentrum, AVV vorhanden | AVV inklusive | Ja |

Die Stärke von DeepSeek liegt im Modell selbst – nicht im chinesischen Cloud-Dienst. Wer die Leistung will, aber den Datenabfluss nicht, hostet das offene Modell in Europa. Technisch ist das heute Standard, kein Sonderprojekt.

## Die Rechnung, die kaum jemand macht

Rechnen wir kurz gegen, was hier wirklich auf dem Spiel steht. Angenommen, du sparst dir mit der kostenlosen Cloud-Version im Monat 200 € gegenüber einem bezahlten EU-Anbieter – über ein Jahr also 2.400 €.

Dem gegenüber steht das Bußgeldrisiko der DSGVO: bis zu 20 Millionen Euro oder 4 % deines weltweiten Jahresumsatzes – je nachdem, welcher Betrag höher ist. Dazu kommt das realistischere Alltagsrisiko: eine Abmahnung, weil ein Wettbewerber oder ein Betroffener den unzulässigen Drittlandtransfer entdeckt, plus der Vertrauensverlust, wenn ein Kunde erfährt, dass seine Daten auf chinesischen Servern gelandet sind.

:::callout Profi-Tipp
Bevor irgendein KI-Tool im Team ausgerollt wird: Kläre eine einzige Frage – "Verlässt personenbezogene Datenverarbeitung damit die EU?" Wenn die Antwort ja oder unklar ist, brauchst du eine andere Lösung oder ein anderes Setup. Diese eine Frage verhindert die meisten teuren Fehler.
:::

Die eingesparten 2.400 € sind schnell weg, wenn nur ein Teil dieser Risiken eintritt. Das ist keine Panikmache – es ist schlicht Erwartungswert-Rechnung.

## Wie du DeepSeeks Stärke nutzt, ohne das Risiko

Du musst nicht zwischen guter KI und Datenschutz wählen. In der Praxis funktionieren drei Wege:

- **Modell in Europa hosten.** DeepSeek R1/V3 auf EU-Infrastruktur betreiben – die Leistung bleibt, die Daten auch. Das ist der sauberste Weg, wenn du die Modellqualität konkret brauchst.
- **Sauber trennen.** Für rein anonyme, nicht personenbezogene Aufgaben (z. B. allgemeine Textbausteine, Code-Snippets ohne Kundenbezug) ist das Risiko gering. Sobald echte Personendaten ins Spiel kommen, greift Regel eins.
- **In eine geprüfte Automatisierung einbetten.** Statt dass 5 Mitarbeiter unkontrolliert Kundendaten in irgendein Chatfenster tippen, läuft die KI in einem definierten, DSGVO-konform aufgesetzten Workflow – mit klarer Datenhaltung und Zugriffskontrolle.

Genau dieser dritte Weg ist der, den wir bei DigitalXShift bauen: KI-gestützte Prozesse auf Infrastruktur, die dir gehört. Wie ein B2B-SaaS-Gründer damit 52 Stunden im Monat aus seinen eigenen Tabellen zurückholte, zeigt diese [Fallstudie](https://www.agenturmarkt.de/agentur/digitalxshift-johannes-kofler-wallerfangen/fallstudien/b2b-saas). Und wie eine 5-köpfige Dev-Agentur 35–50 verlorene Stunden pro Monat wieder abrechenbar machte, liest du [hier](https://www.agenturmarkt.de/agentur/digitalxshift-johannes-kofler-wallerfangen/fallstudien/software-beratung) – in beiden Fällen ohne Datenabfluss in ein Drittland.

## Fazit

DeepSeek ist ein technisch starkes Modell – aber die chinesische Cloud-Version ist für den Geschäftseinsatz mit Kundendaten aktuell ein echtes DSGVO-Risiko. Die Behörden haben 2025 nicht ohne Grund reagiert: fehlender AVV, kein EU-Vertreter, Datenspeicherung in China ohne Opt-out. Die gute Nachricht ist, dass du die Modellqualität trotzdem haben kannst – wenn du es in Europa hostest oder in einen sauber aufgesetzten Workflow packst.

Dein nächster Schritt für diese Woche: Geh einmal ehrlich durch, welche KI-Tools in deinem Team aktuell genutzt werden – auch die inoffiziellen. Bei jedem stell die eine Frage: "Verlassen dabei personenbezogene Daten die EU?" Wo du kein klares Nein hast, hast du deinen ersten Handlungspunkt gefunden. Wenn du dabei Unterstützung willst, [sprich mit uns](https://digitalxshift.com).

:::faq
### Ist DeepSeek in Deutschland verboten?
Nein, nicht pauschal. Aber die Berliner Datenschutzbeauftragte hat die App im Juni 2025 bei Apple und Google zur Prüfung einer Sperrung gemeldet, und die geschäftliche Nutzung mit Personendaten sehen die Aufsichtsbehörden als DSGVO-widrig an.

### Wo speichert DeepSeek meine Daten?
Die Cloud-Version speichert Daten auf Servern in China – inklusive Eingaben, Chatverläufen, Kontaktdaten und Tastatureingabemustern, ohne Opt-out.

### Kann ich DeepSeek überhaupt DSGVO-konform einsetzen?
Die offene Cloud-Version praktisch nicht. Da die Modelle aber quelloffen sind, kannst du sie auf eigener oder europäischer Infrastruktur betreiben – dann bleiben die Daten in deiner Kontrolle.

### Was ist der Unterschied zwischen dem Modell und dem Dienst?
Das Modell (R1/V3) ist die KI selbst und open-weight verfügbar. Der problematische Teil ist der chinesische Cloud-Dienst drumherum. Trennst du beides, nutzt du die Leistung ohne den Datenabfluss.
:::
