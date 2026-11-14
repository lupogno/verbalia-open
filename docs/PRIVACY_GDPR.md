# Privacy, consenso e protezione dati

**Materiale progettuale, non una valutazione d'impatto né consulenza legale.** Riunioni e verbali possono contenere dati personali, sensibili e segreti aziendali.

## Presidi nel prototipo

- La modalità predefinita legge JSON e produce report **localmente**, senza chiamate a provider esterni.
- La chiamata AI richiede dipendenza opzionale, variabile ambiente per chiave API e flag `--allow-external-processing` per ogni comando. La flag certifica soltanto un'intenzione tecnica dell'operatore, **non il consenso né la liceità**.
- Nessuna registrazione occulta, invio automatico di e-mail, firma o upload a GitHub.
- I file di esempio contengono **dati fittizi**.
- Non vengono applicate politiche reali di cifratura, account, separazione tenant, sicurezza per produzioni multiutente o retention: tali capacità sono da sviluppare e verificare prima di un SaaS pubblico.

## Meeting Live

`verbalia live join` inoltra il link della riunione a Recall.ai. L'assistente è visibile e l'acquisizione resta disattivata finché l'operatore non usa `live start`. La trascrizione può richiedere trattamento audio. Video MP4, eventi dei partecipanti e metadati della riunione come artefatti separati sono disattivati. I media generati su Recall hanno una scadenza predefinita di 24 ore dallo stato `done`. Il link e i dati conservati da eventuali subfornitori seguono regole proprie. [Conservazione su Recall.ai](https://docs.recall.ai/docs/storage-and-playback)

L'operatore conferma informativa ed elaborazione esterna sia per l'invito sia per la trascrizione. Prima di trascrivere verifica i presupposti e documenta i consensi dove richiesti. In caso di revoca o mancata autorizzazione, usa `live stop` o fai uscire il bot. Gestisci accesso, conservazione e cancellazione dei file locali in `private/` secondo le regole applicabili alla riunione. La guida [MEETING_LIVE.md](MEETING_LIVE.md) descrive il flusso e i requisiti del ricevitore.

## Prima di usare audio o verbali reali

1. Individuare titolare, eventuale responsabile del trattamento e soggetti autorizzati.
2. Determinare finalità, base giuridica, informativa, minimizzazione, tempi di conservazione, rischi, trasferimenti, condizioni contrattuali e misure di sicurezza.
3. Per registrazioni di assemblea condominiale, verificare attentamente indicazioni del Garante e consenso informato quando richiesto. Non estendere automaticamente la stessa base giuridica a tutti i contesti aziendali.
4. Informare i partecipanti di eventuali strumenti AI e fornitori esterni, gestire accessi, esercizio diritti, rettifiche e cancellazioni.
5. Redigere un registro e una DPIA quando necessaria; far verificare procedure e misure da un professionista privacy.
6. Valutare i requisiti per dati relativi a lavoratori e le regole per strumenti di controllo a distanza.

## Pubblicazione GitHub

**NON caricare mai** credenziali `.env`, registrazioni, trascrizioni reali, copie di verbali condominiali, registri nominativi o dati di fornitori/clienti. `.gitignore` è una rete aggiuntiva, non sostituisce la revisione del contenuto prima del push.

## URL

- https://eur-lex.europa.eu/eli/reg/2016/679/oj
- https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/1297626
- https://www.garanteprivacy.it/
