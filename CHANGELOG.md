# Changelog

## 0.3.1 — 2026-11-14

- Ingresso in videocall senza acquisizione. Usare `live start` per avviare la trascrizione dopo la conferma, `live stop` per fermarla e `live leave` per far uscire il bot.
- Le opzioni lingua, sottotitoli e webhook si impostano ora su `live start`. I media su Recall scadono dopo 24 ore per impostazione predefinita.
- Pannello Streamlit con conferme separate per invito e acquisizione. Webhook con deduplica in memoria anche per richieste simultanee.
- GitHub Actions verifica i test prima di pubblicare lo ZIP della skill e il relativo checksum. L'integrazione Recall è verificata con API simulate.

## 0.3.0 — 2026-11-14

- **Verbalia Live**: integrazione opzionale Recall.ai per partecipante dichiarato in Meet/Zoom/Teams/Webex.
- CLI di join, status, leave, trascrizione, ricevitore webhook real-time con firma e snapshot; UI Streamlit.
- Opt-in obbligatorio prima di richiedere ingresso, MP4 disabilitato per default.
- Test automatici con provider simulato; integrazione live non ancora collaudata con credenziali reali.


## 0.2.0 — 2026-11-14

- Repository originale Agent Skills con modelli per condominio, CDA, cantiere, azienda e associazione.
- Motore di controlli deterministici, audit, verbale e azioni CSV.
- Integrazione OpenAI opzionale con consenso tecnico esplicito per invio esterno.
- Esportazioni di base Markdown, DOCX e PDF; Streamlit locale.
- Esempi fittizi, test automatici, documentazione legale/privacy, GitHub Actions.

## 0.1.0 — prototipo preliminare

- Prima sperimentazione di skill e checklist.
