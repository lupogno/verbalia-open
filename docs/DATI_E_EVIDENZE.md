# Modello dati ed evidenze

Ogni documento `meeting.json` rappresenta **un fascicolo di riunione**, con `sources` e collegamenti `agenda[].evidence` e `actions[].evidence`. Una `evidence` è un ID fonte, non prova di per sé che il contenuto supporti la frase: la verifica del passaggio resta umana.

- `type`: condominio, cda, azienda, cantiere, associazione, altro.
- `attendees`: ogni riga rappresenta un avente diritto al voto o un soggetto registrato per la riunione. In condominio `millesimi` è il valore da attribuire a quell'avente diritto. Le deleghe sono annotate in `represented_by`, senza raddoppiare quote e senza cambiare il voto espresso dall'avente diritto.
- `voters_total`: totale aventi diritto; nei CDA S.p.A. amministratori in carica.
- `convocation`: 1 o 2 (solo condominio).
- `quorum_rule`: da scegliere con motivazione professionale, **mai dedotta automaticamente dal testo di delibera**.
- `outcome`: dichiarazione documentale; `approved` non esiste come flag di validità giuridica.
- `votes`: registrazione uno-a-uno per avente diritto presente, incluse astensioni.
- `sources`: `id`, `description` e `type`; evitare il contenuto integrale di documenti protetti nei metadati.
- `actions`: attività, owner e scadenza; in assenza di owner, campo vuoto e rilievo.

## Miglioramenti successivi

Serve un modello dettagliato per unità immobiliari, contitolarità, usufrutto, partecipazione per singoli punti, cronologia ingressi/uscite e voti modificati durante l'assemblea. Per i CDA serve gestione dei consiglieri interessati, condizioni statutarie e partecipazione a distanza. L'attuale motore è di **pre-screening**.
