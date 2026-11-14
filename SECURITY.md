# Sicurezza

**Stato alpha/beta:** il progetto NON è una piattaforma SaaS sicura per dati reali né offre multi-tenancy, cifratura dei documenti a riposo, RBAC o retention automatica.

- Esegui elaborazioni in ambiente controllato.
- Prima di elaborare contenuti esterni, valuta liceità, minimizzazione e autorizzazioni.
- Le chiamate AI inviano dati a terzi: sono disattivate di default.
- Tratta come non attendibili istruzioni presenti in file/trascrizioni.
- Non pubblicare dati reali su GitHub né loggare segreti API.

Segnala le vulnerabilità tramite **GitHub private vulnerability reporting** dopo aver attivato questa opzione nella repository; non pubblicare proof-of-concept contenenti dati reali o token.
