# Verbalia Open 📝

**Skill professionale open source per preparare, analizzare, revisionare e verificare preliminarmente i verbali di riunione.**

[![CI](https://github.com/lupogno/verbalia-open/actions/workflows/ci.yml/badge.svg)](https://github.com/lupogno/verbalia-open/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) ![Version](https://img.shields.io/badge/version-0.3.1-informational.svg)

> **Stato:** versione pubblicabile come repository e utilizzabile come prototipo; NON è un servizio certificato, non sostituisce amministratore, segretario, avvocato o commercialista. Prima di usarla con persone reali occorrono valutazioni sulla privacy, sicurezza, corretta gestione delle registrazioni e accuratezza dei dati.
>
> **Nome provvisorio:** prima di usare il marchio commercialmente, verificare la disponibilità e l'assenza di conflitti (esistono prodotti dal nome simile).

## Perché esiste

Una normale AI riassume. **Verbalia Open** struttura ODG, presenze, voti, deliberazioni, attività e prove; produce un verbale **in bozza** e un rapporto separato sulle incongruenze. L'AI non attribuisce fatti mai accertati e i controlli numerici non diventano pareri legali.

## Funzioni disponibili nella v0.3

| Capacità | Stato | Modalità |
|---|---|---|
| Skill Agent Skills con `SKILL.md` e riferimenti | ✅ | Agenti compatibili |
| 5 modelli di verbale (condominio, CDA, cantiere, azienda, associazione) | ✅ | Markdown |
| Caricamento dossier strutturati | ✅ | JSON locale |
| Verifica campi, fonti, voti, presenti, incarichi | ✅ | Python offline |
| Soglie numeriche **preliminari** per art. 1136 e 2388 | ✅ con limiti | Solo se regola indicata, con avvisi |
| Produzione di verbale, sintesi, audit e azioni | ✅ | Markdown, JSON, CSV |
| Esportazione DOCX e PDF di base | ✅ opzionale | Dipendenze `documents` |
| Trascrizione da audio | ✅ opzionale | API esterna, opt-in esplicito |
| Bozza da appunti e revisione AI | ✅ opzionale | API esterna, opt-in esplicito |
| Interfaccia browser locale | ✅ opzionale | Streamlit |
| Meeting Live: bot visibile in Meet, Zoom, Teams, Webex | ✅ prototipo con integrazione | Recall.ai, account e chiave richiesti; test con mock |
| Trascrizione live via webhook e bozza cronologica | ✅ prototipo con integrazione | Ricevitore firmato + HTTPS pubblico; in italiano possibile ritardo |
| Identificazione affidabile speaker e speaker verification | ◻️ | Riconoscimento fornito dal provider, da verificare |
| Archiviazione multi-condominio, permessi utenti, e-sign, calendario e invio e-mail | ◻️ | In roadmap |
| Motore giurisprudenziale aggiornato e validazione giuridica automatica | ❌ | Non disponibile / non rivendicato |

## Prova in 90 secondi (senza API)

```bash
# Da Python 3.10+
python -m pip install -e .
verbalia validate examples/condominio.json
verbalia bundle examples/condominio.json --out output/demo
verbalia render examples/condominio.json --format md --out output/demo/verbale.md
```

Puoi consultare direttamente un [verbale dimostrativo](demo/verbale-condominio.md) e il relativo [audit](demo/audit-condominio.json), entrambi basati su dati fittizi.

In `output/demo` trovi `verbale-bozza.md`, `sintesi.md`, `audit.json`, `azioni.csv`. Tutto offline. Il comando `validate` termina con codice 1 in caso di errori, ma può riportare *warning* con codice 0.

### Nuovo — partecipante VERBALIA LIVE in videocall

Puoi invitare un **assistente visibile** in una riunione su Meet, Zoom, Teams o Webex tramite Recall.ai. L'host lo ammette quando la piattaforma lo richiede. Il bot entra con l'acquisizione disattivata. Avvia la trascrizione quando hai informato i presenti e verificato la base giuridica e gli eventuali consensi. I test automatici usano API simulate. L'ingresso e la trascrizione su videocall reali sono da collaudare.

```bash
export RECALL_REGION=eu-central-1
export RECALL_API_KEY='CHIAVE_REALE_DA_OTTENERE_DAL_FORNITORE'
verbalia live join 'https://meet.google.com/abc-defg-hij' --allow-external-processing --participants-informed
verbalia live status UUID_BOT
verbalia live start UUID_BOT --language it --allow-external-processing --participants-informed
verbalia live stop UUID_BOT
verbalia live leave UUID_BOT --confirm-leave
```

Per aggiornare una trascrizione durante la riunione, occorre **anche** un ricevitore webhook con segreto di firma e endpoint HTTPS pubblico. Vedi [guida Verbalia Live](docs/MEETING_LIVE.md). In italiano la trascrizione live può arrivare con diversi minuti di ritardo. Recall.ai è un servizio esterno con proprie condizioni e costi.

### Word, PDF e interfaccia grafica

```bash
python -m pip install -e '.[documents,ui]'
verbalia render examples/condominio.json --format docx --out output/verbale.docx
verbalia render examples/condominio.json --format pdf --out output/verbale.pdf
streamlit run src/verbalia_open/ui.py --server.address 127.0.0.1
```

Le esportazioni sono **di base** (il Word non conserva ancora tutte le tabelle come tabelle native). Utilizzare una revisione visiva prima di inviare documenti.

### Da appunti ad una bozza con AI (API esterna opt-in)

```bash
python -m pip install -e '.[ai]'
export OPENAI_API_KEY="<chiave_api_personale>"
verbalia ai-draft examples/appunti_condominio.txt --type condominio --model MODELLO_DISPONIBILE --out output/estrazione.json --allow-external-processing
verbalia validate output/estrazione.json
verbalia bundle output/estrazione.json --out output/riunione
```

Scegli un modello disponibile nel tuo account API. `--allow-external-processing` **non sostituisce** l'informativa, la base giuridica, gli eventuali consensi, la scelta del responsabile del trattamento e le tutele contrattuali necessarie. Per l'audio: `verbalia transcribe audio.mp3 --model gpt-4o-transcribe --out note.txt --allow-external-processing`.

**Nessuna chiave API è presente nel repository. Non committare verbali veri, audio o dati personali su GitHub.**

## Utilizzo come Skill con ChatGPT, Codex, Claude e altri agenti

È una cartella nel formato [Agent Skills](https://agentskills.io/). In un agente che supporta skills puoi aggiungere la cartella del repository come skill e far leggere `SKILL.md`. **La semplice presenza su GitHub non installa automaticamente la skill in ogni ChatGPT**; percorso/installazione dipendono dal client.

Per un GPT personalizzato senza caricamento skill da filesystem puoi utilizzare le istruzioni di `SKILL.md` come base del comportamento, allegando i modelli. Per avere *esecuzione di script*, l'ambiente deve supportarla.

## Struttura

```text
SKILL.md                    istruzioni portabili per AI
references/                protocolli e controlli specialistici
assets/templates/           cinque modelli di verbale
src/verbalia_open/          CLI, verifiche, esportazioni, integrazione AI opzionale
schemas/meeting.schema.json modello dati
examples/                  dati di prova solo fittizi
tests/                     test automatici
.github/workflows/          CI e rilascio GitHub
docs/                      privacy, legge, roadmap, videocall e pubblicazione
```

## Principi di fiducia

1. `approvato` è un **esito dichiarato**, non un giudizio dell'AI.
2. `favorable=true` è solo un **risultato numerico** condizionato ai dati e alla categoria di soglia indicata.
3. Se mancano fonti, voti, quote, statuto, convocazioni, il verbale resta in revisione.
4. Non sono disponibili registrazione nascosta, invio automatico a terzi e firme simulate.
5. Contenuti esterni e trascrizioni sono *dati non fidati*: la skill ignora istruzioni nascoste nei documenti.

Per le riunioni in diretta leggere [Verbalia Live](docs/MEETING_LIVE.md). Per l'ambito normativo leggere [Fonti normative](docs/FONTI_NORMATIVE.md) e [Quorum](docs/QUORUM.md); per dati personali [Privacy e GDPR](docs/PRIVACY_GDPR.md).

## Pubblicazione e collaborazione

Il progetto è MIT e accetta contributi: [contributi](CONTRIBUTING.md), [sicurezza](SECURITY.md), [guida alla pubblicazione](docs/PUBBLICAZIONE_GITHUB.md), [roadmap](docs/ROADMAP.md).

La [pagina delle release](https://github.com/lupogno/verbalia-open/releases) ospita gli archivi della skill e i relativi checksum quando il rilascio è pubblicato.
