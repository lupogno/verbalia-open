# Quale strumento per quale verbale?

Confronto delle funzionalità documentate al **14 novembre 2026**. Le descrizioni degli altri prodotti provengono dalle pagine dei fornitori. Le verifiche riproducibili riguardano Verbalia Open v0.3.1 e i suoi esempi fittizi.

| Strumento | Funzioni documentate | Quando valutare Verbalia Open | Fonte |
|---|---|---|---|
| **Fireflies** | Note con timestamp, sintesi, attività e domande sui meeting con AskFred. | Per verificare una delibera a partire da un dossier di presenze, voti, fonti e regole dichiarate. | [Sintesi](https://guide.fireflies.ai/articles/9547055509-fireflies-ai-meeting-summaries) · [AskFred](https://guide.fireflies.ai/articles/6556345325-askfred-get-answers-from-a-specific-meeting-in-fireflies-and-get-answers) |
| **Otter** | Trascrizione delle riunioni, sintesi e ricerca nelle conversazioni. | Per lavorare offline su un dossier già disponibile e produrre audit e documenti da revisionare. | [Otter Meeting Agent](https://otter.ai/) |
| **MeetGeek** | Sintesi personalizzabili, highlight associati a clip e trascrizione, condivisione. | Per riportare nel verbale votazioni, delibere e incarichi, con esiti numerici distinti dall’esito dichiarato. | [Highlight e sintesi](https://support.meetgeek.ai/en/articles/6021900-highlights-summaries) · [Personalizzazione](https://support.meetgeek.ai/en/articles/10493568-meeting-summary-customization) |
| **VerbaliAI** | Verbalizzazione AI integrata in un gestionale condominiale con contabilità, portali e gestione assemblee. | Per usare un componente portabile su più tipi di riunione, anche indipendentemente dal gestionale dello studio. | [VerbaliAI](https://verbaliai.it/) |
| **CondominioDoc AI** | Ricerca giurisprudenziale con fonti, redazione di atti e verbali, calcolatori di millesimi e quorum. | Per rieseguire controlli su presenze, voti e fonti nello stesso dossier, con codice MIT e un audit JSON esportabile. | [CondominioDoc AI](https://condominiodoc.ai/) |
| **Verbale.online** | Bozze da registrazioni con ordine del giorno, voti nominativi, millesimi e passaggi da verificare. | Per partire da un dossier strutturato, ispezionare le regole di controllo e integrare il motore in un flusso locale. | [Verbale.online](https://verbale.online/) |

## Come verificare il vantaggio sul campo

1. Apri il [dossier fittizio](../examples/caso_critico.json) in cui un esito dichiarato come approvato ha voti incompleti e nessuna fonte associata alla decisione.
2. Esegui `verbalia validate examples/caso_critico.json --json`. Il report lascia il risultato numerico indeterminato, segnala il voto mancante e indica i campi da verificare.
3. Confronta il report con il [codice dei controlli](../src/verbalia_open/engine.py), i [test](../tests/) e la [demo nel README](../README.md).

I grafici del progetto misurano i test e i rilievi dei casi di esempio. Qualità della trascrizione, velocità e risparmio di tempo richiederebbero una prova comparativa con gli stessi input e criteri. I controlli di Verbalia Open sono preliminari e l’approvazione del verbale spetta alle persone autorizzate.
