# Roadmap

## v0.3 — Verbalia Live (prototipo implementato, **non collaudato su account reali**)
- [x] Ingresso bot visibile con provider esterno (Recall.ai) dopo opt-in esplicito
- [x] Stato, uscita, programmazione e recupero trascrizioni tramite API
- [x] Ricevitore webhook firmati e snapshot cronologico con ID fonte
- [x] Pannello Streamlit per ingresso, stato, uscita e snapshot
- [x] Test offline/mock di REST, firma webhook e gestione eventi
- [ ] Collaudo end-to-end con account di prova e partecipanti informati
- [ ] Deployment backend stabile, storage cifrato, retention, gestione webhook persistente
- [ ] Interazione vocale bot e moderazione sotto controllo umano

## v0.2 — prototipo pubblicabile (presente)
- [x] Skill portabile standard Agent Skills
- [x] Modelli per 5 contesti
- [x] CLI offline per audit numerici e coerenza
- [x] Evidenze, verbale, sintesi, registro attività
- [x] AI esterna opt-in per appunti, review e trascrizioni
- [x] Esportazioni Word/PDF basilari e interfaccia locale
- [x] Test CI e release workflow GitHub

## v0.3 — qualità documentale
- [ ] Riconciliazione fonti a livello di frase, pagina e timestamp
- [ ] Confronto revisioni v1/v2 e redline DOCX
- [ ] Verifica fine di deleghe, quote e cambi di presenti per singolo punto
- [ ] Template grafici Word professionali, PDF/A ove richiesto
- [ ] Diarizzazione audio con identificazione assistita e conferma speaker
- [ ] Esempi di benchmark anonimizzati e valutazione con esperti

## v0.4 — studio professionale
- [ ] Archivio multi-condominio, RBAC e audit append-only
- [ ] Ricerche tra verbali precedenti e recupero delle decisioni
- [ ] Connettori autorizzati Drive, Calendar, e-mail (mai invio non approvato)
- [ ] Scadenzario, follow-up e notifiche
- [ ] Policy retention e data residency implementate e testate

## v1.0 — distribuzione professionale
- [ ] Hardening sicurezza, DPIA/DPA ove necessari
- [ ] Pareri giuridici e regole aggiornate con fonti e revisione legale
- [ ] Interfaccia multiutente e flussi approvativi
- [ ] Test estesi con casi reali lecitamente anonimizzati
- [ ] Manuale amministratore, contratti, log, osservabilità
