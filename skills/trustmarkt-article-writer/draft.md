Du kennst das Gefühl: Ein KI-Notiztool klinkt sich in jedes Kundengespräch ein, schreibt mit, fasst zusammen und schickt dir am Ende sauber die To-dos. Fireflies, Otter oder tl;dv übernehmen die lästige Protokollarbeit, und du kannst dich im Call endlich voll auf den Kunden konzentrieren. Fühlt sich an wie ein unfairer Vorteil.

Der Haken: Bevor so ein Tool mitschreibt, passieren zwei Dinge gleichzeitig, die die meisten nie prüfen. Erstens nimmst du die Stimme einer anderen Person auf – und das ist in Deutschland nicht nur eine Datenschutzfrage, sondern kann strafbar sein. Zweitens wandert die Aufnahme oft auf US-Server zu einem Anbieter, mit dem du keinen sauberen Vertrag hast. Dieser Artikel zeigt dir, wo die echten Risiken liegen und wie du KI-Meeting-Tools einsetzt, ohne dir rechtlich das Genick zu brechen.

## Der Haken, den fast niemand auf dem Schirm hat: § 201 StGB

Bevor die DSGVO überhaupt ins Spiel kommt, gibt es eine deutlich härtere Hürde – das Strafrecht. § 201 StGB schützt die "Vertraulichkeit des Wortes". Wer das nicht öffentlich gesprochene Wort eines anderen unbefugt auf einen Tonträger aufnimmt, macht sich strafbar – mit Freiheitsstrafe bis zu drei Jahren oder Geldstrafe.

Das Entscheidende, das kaum jemand weiß: Das gilt auch dann, wenn du selbst am Gespräch beteiligt bist. Du darfst ein vertrauliches Gespräch also nicht einfach mitschneiden, nur weil du einer der Teilnehmer bist. Und ob der Inhalt harmlos ist, spielt keine Rolle – geschützt ist das gesprochene Wort an sich, sobald es nicht für die Öffentlichkeit bestimmt ist.

Für dich heißt das: Startest du ein KI-Notiztool in einem Kundencall, ohne dass dein Gegenüber der Aufnahme zugestimmt hat, riskierst du im schlimmsten Fall eine Strafanzeige. Heimliche Aufnahmen sind vor Gericht außerdem regelmäßig gar nicht verwertbar – der vermeintliche Beweis ist dann wertlos.

:::callout Achtung
Ein KI-Meeting-Tool ohne klare Zustimmung aller Teilnehmer mitlaufen zu lassen, ist kein Datenschutz-Lapsus, sondern potenziell eine Straftat nach § 201 StGB. Zustimmung einholen ist deshalb nicht optional, sondern die Grundvoraussetzung.
:::

## Die DSGVO ist die zweite Hürde – und die hat es in sich

Ist die Zustimmung geklärt, kommt die DSGVO dazu. Eine Transkription enthält personenbezogene Daten – Namen, Aussagen, manchmal sensible Geschäftsinterna. Drei Punkte musst du hier sauber haben:

**Rechtsgrundlage und Einwilligung.** Du brauchst eine klare Grundlage für die Verarbeitung. In der Praxis läuft das meist über die ausdrückliche Einwilligung aller Gesprächsteilnehmer zu Beginn des Calls – transparent und dokumentiert, nicht als Fußnote im Kleingedruckten.

**Auftragsverarbeitungsvertrag (AVV).** Der Tool-Anbieter verarbeitet deine Daten in deinem Auftrag. Ohne abgeschlossenen AVV ist der Einsatz formal nicht DSGVO-konform – egal wie gut das Tool ist. Viele Anbieter stellen den AVV nur auf Anfrage oder erst ab dem Business-/Enterprise-Tarif bereit.

**Serverstandort und US-Transfer.** Landet die Aufnahme auf US-Servern, ist das ein Drittlandtransfer mit allen bekannten Risiken. Das ist derselbe Haken, den wir schon bei vielen KI-Diensten gesehen haben – beim heimlichen Mitschnitt von Gesprächen wiegt er nur schwerer, weil es um die Stimmen Dritter geht.

## Die drei großen Tools im DSGVO-Check

Die drei meistgenutzten KI-Meeting-Assistenten unterscheiden sich an genau den Stellen, die rechtlich zählen: Wo liegen die Daten, trainiert der Anbieter damit seine Modelle, und bekommst du einen AVV? Der Überblick:

| Tool | Serverstandort | Training auf deinen Daten | AVV | Preis (pro Nutzer/Monat) |
| --- | --- | --- | --- | --- |
| **Fireflies.ai** | USA (Private Storage in EU nur Enterprise) | Laut Anbieter vertraglich ausgeschlossen | Ja, meist erst ab Enterprise / auf Anfrage | ab ca. 10 $ (Jahr) |
| **Otter.ai** | USA (AWS) | Ja – trainiert eigene Modelle auf de-identifizierten Aufnahmen | Auf Anfrage | Pro ca. 17 $, Business ca. 30 $ |
| **tl;dv** | EU (Google Cloud, AWS, Hetzner, ISO 27001) | Nein, EU-AI-Act-konform | Ja | Pro ca. 18 $, Business ca. 59 $ |

Das Muster ist deutlich: **Fireflies und Otter verarbeiten standardmäßig in den USA**, Otter trainiert sogar die eigenen Modelle auf den Aufnahmen und Transkripten – auch wenn de-identifiziert, ist das für viele deutsche Unternehmen ein Ausschlusskriterium. **tl;dv** ist ein europäischer Anbieter mit Sitz in Portugal, hostet die Daten in EU-Rechenzentren und wirbt mit SOC-2- und EU-AI-Act-Konformität. Für den deutschen Markt ist das die mit Abstand saubere Ausgangslage.

:::callout Profi-Tipp
Wenn du die Wahl noch frei hast, starte mit einem EU-Anbieter wie tl;dv – dann fällt der komplette US-Transfer-Komplex weg und du sparst dir die juristische Dauerbaustelle. Das ist günstiger als jeder nachträgliche Rechtsstreit.
:::

## Besonders heikel: vertrauliche Gespräche

Je sensibler dein Geschäft, desto größer das Risiko. Eine M&A-Boutique, die Verkaufsgespräche mit Investoren führt, oder eine Beratung, die tief in den Zahlen ihrer Mandanten steckt, kann sich einen unbedachten Mitschnitt schlicht nicht leisten – hier geht es um echte Vertraulichkeit, nicht um ein Meeting-Protokoll.

Genau deshalb gewinnt Automatisierung hier doppelt, wenn sie sauber aufgesetzt ist: Prozesse, die ohne heimliche Aufnahmen auskommen und trotzdem Zeit sparen. Wie eine M&A-Boutique ihre Folgeprozesse automatisiert hat, ohne an der Vertraulichkeit zu rütteln, zeigt diese Fallstudie: [M&A-Boutique](https://www.agenturmarkt.de/agentur/digitalxshift-johannes-kofler-wallerfangen/fallstudien/ma-beratungsboutique). Und wie eine Dev-Agentur verlorene Stunden zurückgewinnt, ohne rechtliche Grauzonen zu betreten, liest du hier: [Dev-Agentur](https://www.agenturmarkt.de/agentur/digitalxshift-johannes-kofler-wallerfangen/fallstudien/software-beratung).

## Was du konkret tun musst, bevor das nächste Tool mitschreibt

1. **Zustimmung zuerst.** Hol dir am Anfang jedes Calls die ausdrückliche Einwilligung aller Teilnehmer zur Aufnahme – sichtbar, nicht versteckt. Kein Ja, kein Mitschnitt.
2. **AVV abschließen.** Prüfe, ob dein Anbieter einen Auftragsverarbeitungsvertrag bietet und schließ ihn ab, bevor das Tool live geht. Fehlt er, ist der Einsatz nicht konform.
3. **Serverstandort klären.** Bevorzuge EU-Hosting. Bei US-Tools prüfst du, ob und wie ein rechtssicherer Transfer möglich ist – und ob sich der Aufwand lohnt.
4. **Training abschalten.** Stell sicher, dass der Anbieter deine Aufnahmen nicht zum Modelltraining nutzt – vertraglich, nicht nur per Häkchen.
5. **Löschkonzept festlegen.** Definiere, wie lange Transkripte gespeichert werden und wann sie automatisch gelöscht werden.

:::callout Kernbotschaft
KI-Meeting-Tools sparen echte Zeit – aber nur, wenn Zustimmung, AVV und Serverstandort vorher geklärt sind. Wer einfach drauflos mitschneidet, tauscht eine halbe Stunde Protokoll gegen ein Strafrechts- und DSGVO-Risiko. Das ist kein guter Deal.
:::

## Fazit

KI-Notiztools sind großartig – aber in Deutschland gelten für das Mitschneiden von Gesprächen zwei Regeln gleichzeitig: das Strafrecht (§ 201 StGB) und die DSGVO. Die Zustimmung aller Teilnehmer ist die nicht verhandelbare Basis, ein AVV und ein geklärter Serverstandort der Rest. Bei der Tool-Wahl hat ein EU-Anbieter wie tl;dv für den deutschen Markt klar die Nase vorn, während Fireflies und Otter zusätzlichen Prüfaufwand bedeuten.

Schau dir diese Woche einmal ehrlich an, welches Tool gerade in deinen Calls mitläuft – und ob du für genau dieses Tool die Zustimmung, den AVV und den Serverstandort wirklich geklärt hast. Wenn du bei einem Punkt zögerst, hast du dein nächstes To-do gefunden. Wie du Prozesse automatisierst, ohne in solche Grauzonen zu geraten, besprichst du am besten direkt mit den Profis: [DigitalXShift](https://digitalxshift.com).

:::faq
### Darf ich ein Kundengespräch mit einem KI-Tool aufnehmen, wenn ich selbst teilnehme?
Nein, nicht automatisch. § 201 StGB schützt das vertrauliche Wort auch gegenüber Gesprächsteilnehmern. Ohne Zustimmung aller Beteiligten ist die Aufnahme potenziell strafbar.

### Reicht es, die Aufnahme am Anfang kurz zu erwähnen?
Eine bloße Erwähnung reicht nicht. Du brauchst eine aktive, nachweisbare Zustimmung aller Teilnehmer – und datenschutzrechtlich eine saubere Rechtsgrundlage plus AVV mit dem Anbieter.

### Welches KI-Meeting-Tool ist für deutsche Unternehmen am ehesten DSGVO-konform?
tl;dv als EU-Anbieter mit EU-Hosting bietet die beste Ausgangslage. Fireflies und Otter verarbeiten standardmäßig in den USA und erfordern mehr Prüfaufwand beim Datentransfer.

### Was passiert mit meinen Daten beim Modelltraining?
Otter trainiert eigene Modelle auf de-identifizierten Aufnahmen. Fireflies schließt das laut eigenen Angaben vertraglich aus, tl;dv nutzt deine Daten nicht fürs Training. Prüfe das immer vertraglich, nicht nur in den Einstellungen.
:::
