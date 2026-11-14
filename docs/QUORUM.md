# Quorum: modello numerico prudenziale

**ATTENZIONE:** Nessun controllo numerico equivale a validità della delibera. Questo modulo è pensato per individuare **anomalie**.

## Condominio, riferimento art. 1136 c.c. (Italia)

Semplificazione per situazioni ordinarie con un diritto di voto per testa rappresentata, tabelle valide e millesimi correttamente attribuiti. Non risolve controversie di comproprietà, condomìni parziali, supercondomini, deleghe irregolari, assenze giustificate o leggi speciali.

- 1ª convocazione: soglia costituzione **maggioranza dei partecipanti** e **almeno 2/3 valore**; deliberazione ordinaria maggioranza intervenuti e **almeno 1/2 valore**.
- 2ª convocazione: costituzione **almeno 1/3 partecipanti** e **almeno 1/3 valore**; deliberazione ordinaria **maggioranza intervenuti** e **almeno 1/3 valore**.
- Materie particolari: soglie da qualificare e controllare caso per caso. Se una materia richiede **maggioranza intervenuti e 1/2** o **maggioranza intervenuti e 2/3** del valore, `quorum_rule=meta_valore` o `due_terzi_valore` applica solo il calcolo indicato.
- `quorum_rule=manuale` è il valore prudenziale da usare senza accertamento della categoria della proposta.

**I millesimi nel prototipo sono una tabella per votante/avente diritto e non una rappresentazione completa dei diritti reali su ogni unità.** Non usare per validazioni definitive.

## CDA S.p.A., riferimento art. 2388 c.c.

- Calcolo base: presenza **maggioranza degli amministratori in carica**; delibera **maggioranza assoluta dei presenti**.
- Non sono ammessi voti per rappresentanza nella fattispecie disciplinata dall'articolo.
- **Statuto e tipo societario:** l'app richiede una verifica esplicita. Per S.r.l. non applicare automaticamente lo stesso controllo legale.
- Testo art. 2388 modificato dal 29 aprile 2026: riferirsi sempre alla versione vigente.

## Significato dei campi dell'audit

- `constituted: true`: superata la soglia **numerica** prevista dal profilo impostato; nessun attestato di validità.
- `favorable: true`: superata la soglia **numerica** di voto secondo i dati dichiarati.
- `null`: non verificato, per dati o regole mancanti.
- `status: da_verificare`: almeno un rilievo oppure una verifica indeterminata.

## Casi NON implementati

Controllo dell'ordine del giorno, decorrenza termini convocazione, validità delle deleghe, speciale titolarità e nuda proprietà/usufrutto, esclusioni dal voto, conflitti, fondi speciali, quorum speciali, statuti complessi, impugnazioni e certificazione giuridica. Un professionista deve valutare la casistica.
