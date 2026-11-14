# Pubblicare Verbalia Open su GitHub

## Verificare il destinatario

La destinazione prevista è `lupogno/verbalia-open`. Autenticati con GitHub CLI e verifica l'account con `gh api user --jq .login`. Controlla le repository di tua proprietà con `gh repo list lupogno` e cerca quella prevista con `gh repo view lupogno/verbalia-open`. Un errore di autenticazione o permessi va risolto prima di procedere. Se esiste già, esamina contenuti, branch e tag prima di decidere come integrare il progetto.

## Preparare il primo push

Esegui questi comandi dalla radice estratta dello ZIP. Gli esempi inclusi sono fittizi. Controlla l'elenco dei file prima del commit e tieni chiavi, registrazioni e dati privati fuori dalla repository.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/check_repo.py
git init -b main
git add --all
git diff --cached --stat
git commit -m "Publish Verbalia Open v0.3.1"
```

Se il nome è disponibile e la creazione è autorizzata, crea la repository pubblica e invia il branch `main`:

```bash
gh auth refresh --hostname github.com --scopes workflow
gh repo create lupogno/verbalia-open --public --source=. --remote=origin --push
```

## Rilasciare la skill

Controlla l'esito di CI sulla pagina **Actions**. Dopo il passaggio dei test, crea e invia un tag uguale alla versione Python con prefisso `v`:

```bash
git tag -a v0.3.1 -m "Verbalia Open v0.3.1"
git push origin v0.3.1
```

Il workflow di release verifica il tag e riesegue i test, quindi pubblica le note della versione, lo ZIP della skill e il checksum SHA-256. Verifica i file su [GitHub Releases](https://github.com/lupogno/verbalia-open/releases). Per generare lo ZIP localmente usa `python tools/package_skill.py`.

I workflow GitHub usano esempi fittizi e mock. Per il collaudo separato con Recall.ai, configura le credenziali nell'ambiente locale o nel gestore di segreti del servizio che ospita il ricevitore, seguendo [Verbalia Live](MEETING_LIVE.md) e [Privacy e GDPR](PRIVACY_GDPR.md).
