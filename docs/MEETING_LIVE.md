# Verbalia Live — assistente in videocall

**Stato:** integrazione software implementata e testata con mock; non ancora collaudata su una conferenza reale. Non si connette automaticamente a Zoom/Meet/Teams quando si legge `SKILL.md`. L'operatore deve configurare e autorizzare un provider esterno. È un bot dichiarato, non si presenta come persona fisica e non emette automaticamente interventi vocali.

## Funzioni implementate

| Comando | Effetto |
|---|---|
| `verbalia live join` | Richiede l'ingresso di un assistente visibile con acquisizione disattivata. L'host può doverlo ammettere. |
| `verbalia live status` | Consulta manualmente lo stato di una singola istanza; per sistemi professionali usare webhook di stato |
| `verbalia live start` | Avvia la trascrizione dopo le conferme dell'operatore |
| `verbalia live stop` | Arresta l'acquisizione lasciando l'assistente in riunione |
| `verbalia live leave` | Allontana il bot, con conferma |
| `verbalia live serve` | Riceve eventi di trascrizione in tempo reale, firma HMAC verificata, timestamp, limitazione ai bot autorizzati |
| `verbalia live snapshot` | Converte eventi in trascrizione con identificatori TR e segnalazioni lessicali da verificare |
| `verbalia live transcript` | Recupera la trascrizione normalizzata dopo la generazione dell'artefatto, se disponibile |
| `streamlit run src/verbalia_open/ui.py --server.address 127.0.0.1` | Scheda **Meeting Live** per ingresso, stato, avvio, arresto, uscita e lettura snapshot |

## Prerequisiti e privacy

1. Account sul servizio [Recall.ai](https://www.recall.ai/) e chiave API: il servizio è esterno, può prevedere costi, termini e contratti propri. Preferire regione `eu-central-1` se appropriata, verificando comunque trasferimenti, retention e subfornitori.
2. L'operatore deve avere titolo per invitare l'assistente. I partecipanti devono ricevere informativa adeguata e devono essere verificati i presupposti per registrazione, trascrizione, eventuale consenso o altre basi giuridiche, secondo contesto e normativa. In certi meeting può non essere lecito farlo.
3. Nessuna identità di persona reale viene simulata. L'assistente deve essere visibile nell'elenco partecipanti con un nome esplicito. La piattaforma può richiedere ammissione dalla sala d'attesa; nessun bypass.
4. Le chiavi API e il segreto webhook vanno gestiti mediante variabili ambiente/secrets manager. **Mai inserire in repository, link pubblici, esempi o screenshot.**
5. Per il live sono necessari backend in esecuzione e URL HTTPS pubblico *stabile*: `localhost` da solo non è raggiungibile dal servizio. Preferire reverse proxy HTTPS con autenticazione sull'interfaccia amministrativa, rate limiting e log minimizzati.

## Configurare

```bash
python -m pip install -e '.[ui]'
export RECALL_REGION=eu-central-1
export RECALL_API_KEY='LA_TUA_CHIAVE_REALE'    # solo nel terminale o secrets manager, non nel file repository
export RECALL_WORKSPACE_VERIFICATION_SECRET='whsec_IL_TUO_SEGRETO'
```

I valori sopra sono segnaposto. Per un test senza webhook, avvia la trascrizione dopo l'ingresso e scaricala quando l'artefatto è pronto. Per ricevere eventi durante la conferenza, prepara il proxy HTTPS e avvia il ricevitore dopo aver ottenuto l'ID del bot:

```bash
# Dopo aver ottenuto un ID con 'live join' (oppure usarne uno già noto)
verbalia live serve --host 127.0.0.1 --port 8787 --bot-id UUID_BOT --out private/events.jsonl
# Esponi con reverse proxy HTTPS pubblico stabile il path /recall/events verso 127.0.0.1:8787.
```

Prima di usare `live start --webhook-url`, verifica che il ricevitore sia attivo per quell'ID. Il ricevitore verifica firma e ID del bot e deduplica gli eventi fino al successivo riavvio. Conserva eventi e trascrizioni in una directory privata con accesso limitato. Configura limiti di traffico e tempi di risposta sul proxy.

### Attivazione durante un meeting già iniziato

```bash
verbalia live join 'https://meet.google.com/abc-defg-hij' \
  --allow-external-processing \
  --participants-informed
```

Il comando restituisce l'**ID del bot**. Verifica l'ingresso con `live status` e attendi l'ammissione quando richiesta. Puoi anche programmare l'ingresso:

```bash
verbalia live join 'https://zoom.us/j/123456789' --join-at '2026-12-03T10:00:00+01:00' \
  --allow-external-processing --participants-informed
```

```bash
verbalia live status UUID_BOT
verbalia live start UUID_BOT --language it --allow-external-processing --participants-informed
verbalia live snapshot --events private/events.jsonl --bot-id UUID_BOT --out private/trascrizione-live.md
verbalia live stop UUID_BOT
verbalia live leave UUID_BOT --confirm-leave
# Una volta creato l'artefatto transcript (transcript.done):
verbalia live transcript UUID_BOT --out private/trascrizione-finale.md
```

Usa `live start` dopo aver informato chi è presente e verificato i presupposti e gli eventuali consensi. Per ricevere gli eventi aggiungi `--webhook-url https://TUO_DOMINIO/recall/events` a `live start`. Informa anche chi entra a riunione iniziata. Se manca un'autorizzazione necessaria o viene revocata, usa `live stop` oppure fai uscire l'assistente. L'arresto lascia completare l'elaborazione del materiale già acquisito. Verifica lo stato prima di ripetere `live start`, perché Recall può riavviare la registrazione in corso.

Per trasformare le note in un verbale strutturato, **solo dopo revisione delle fonti**:

```bash
verbalia ai-draft private/trascrizione-finale.md --type condominio \
  --model MODELLO_DISPONIBILE --out private/bozza.json --allow-external-processing
verbalia validate private/bozza.json
verbalia bundle private/bozza.json --out private/verbale
```

Quest'ultimo comando `ai-draft` attiva un **secondo trattamento esterno** con API AI: deve essere valutato e autorizzato separatamente. Per un flusso locale usare invece il JSON redatto e revisionato dall'operatore, seguito da `bundle`.

## Lingua, ritardi e limiti

- **Italiano (`--language it`, predefinito):** modello `recallai_streaming`, modalità `prioritize_accuracy`, può accumulare ritardo di circa **3–10 minuti** per gli eventi in diretta. Il ritardo dipende dal servizio e dalla call.
- **Inglese (`--language en`):** `prioritize_low_latency`, in genere 1–3 secondi dopo la frase, con restrizioni di supporto lingua e funzionalità.
- **`--captions`:** usa le didascalie native quando disponibili; qualità e disponibilità dipendono dal meeting, dall'account e dal provider.
- Nessun calcolo di quorum o delibera può essere ricavato automaticamente da una frase riconosciuta. Le frasi candidate rimangono `DA VERIFICARE`.
- Il bot è **ascoltatore/verbalizzante**. Interventi vocali, moderazione e assistente che risponde a domande sono possibili come progetto successivo, previa progettazione dei permessi e di un'interfaccia conversazionale.
- Non sono garantiti tempi di ingresso, disponibilità della trascrizione, corretto riconoscimento speaker, capacità del bot di essere ammesso, né servizio utilizzabile su ogni account/riunione.
- Per minimizzare i dati, la richiesta disattiva il video MP4 e gli artefatti separati di eventi dei partecipanti e metadati della riunione. L'audio può essere trattato per generare la trascrizione. I media generati su Recall scadono dopo 24 ore dallo stato `done`, salvo diversa durata indicata con `--retention-hours`. Verifica anche conservazione di link, copie locali e dati presso eventuali subfornitori.

## Restrizioni sulle API native (verificato 14 novembre 2026)

- **Google Meet:** la Meet Media API Developer Preview è stata dismessa come percorso futuro: nuove iscrizioni chiuse, spegnimento il **15 gennaio 2027**. Non costruire su quell'API come integrazione nativa di lungo periodo.
- **Microsoft Teams:** Microsoft non raccomanda bot Real-Time Media applicativi generici per agenti AI di riunione; indica Copilot Studio e Graph transcripts come percorsi preferiti.
- **Zoom:** le condizioni d'uso pubblicate per Meeting SDK e bot sono in evoluzione. Utilizzare un provider per meeting bot conforme, oppure le soluzioni approvate come RTMS, evitando di presumere che una login SDK standard autorizzi notetaker.

## Riferimenti API

- https://docs.recall.ai/docs/bot-overview
- https://docs.recall.ai/reference/bot_create
- https://docs.recall.ai/reference/bot_retrieve
- https://docs.recall.ai/reference/bot_leave_call_create
- https://docs.recall.ai/docs/recording-control
- https://docs.recall.ai/docs/storage-and-playback
- https://docs.recall.ai/docs/bot-real-time-transcription
- https://docs.recall.ai/docs/authenticating-requests-from-recallai
- https://docs.recall.ai/docs/real-time-event-payloads
- https://docs.recall.ai/docs/download-schemas
- https://developers.google.com/workspace/release-notes
- https://learn.microsoft.com/en-us/microsoftteams/platform/bots/calls-and-meetings/real-time-media-concepts
- https://developers.zoom.us/docs/meeting-sdk/
