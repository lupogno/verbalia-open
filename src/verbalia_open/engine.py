"""Controlli deterministici preliminari. Non certificano validità legale."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import date

KINDS = {"condominio", "cda", "azienda", "cantiere", "associazione", "altro"}
VOTES = {"favorevole", "contrario", "astenuto"}
RULES = {"ordinaria", "meta_valore", "due_terzi_valore", "manuale"}


def issue(code: str, level: str, message: str, path: str = "") -> dict:
    return {"code": code, "level": level, "message": message, "path": path}


def decimal(value, field):
    try:
        n = Decimal(str(value))
        if not n.is_finite():
            raise ValueError
        return n
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field}: valore numerico non valido")


def _numeric_thresholds(kind, convocation, total, present, n_total, n_present, n_favor, favor_milli, rule):
    """Ritorna solo esito aritmetico della regola specificata dall'utente."""
    if kind == "condominio":
        if convocation not in (1, 2):
            return None, None, "Convocazione non indicata"
        if rule == "manuale":
            return None, None, "Regola di maggioranza da qualificare per legge"
        if convocation == 1:
            constituted = (n_present * 2 > n_total and present * 3 >= total * 2)
            min_milli = total / 2
        else:
            constituted = (n_present * 3 >= n_total and present * 3 >= total)
            min_milli = total / 3
        if rule == "meta_valore":
            min_milli = total / 2
        if rule == "due_terzi_valore":
            min_milli = total * 2 / 3
        favorable = n_favor * 2 > n_present and favor_milli >= min_milli
        return constituted, favorable, "Soglie aritmetiche art. 1136 c.c. (profilo dichiarato); verifica giuridica necessaria"
    if kind == "cda":
        if rule == "manuale":
            return None, None, "Regole statutarie o societarie non confermate"
        constituted = n_present * 2 > n_total
        favorable = n_favor * 2 > n_present
        return constituted, favorable, "Soglie base art. 2388 c.c. per S.p.A.; verificare statuto, tipo societario e materie"
    return None, None, "Nessuna soglia legale predefinita: configurare regole applicabili"


def assess(data: dict) -> dict:
    issues = []
    results = []
    if not isinstance(data, dict):
        return {"status": "da_verificare", "issues": [issue("INVALID_ROOT", "error", "Il documento deve essere un oggetto JSON")], "resolutions": []}
    kind = data.get("type")
    if kind not in KINDS:
        issues.append(issue("MEETING_TYPE", "error", f"Tipo riunione non riconosciuto: {kind!r}", "type"))
    for key in ("title", "date", "location", "chair", "secretary"):
        if not data.get(key):
            issues.append(issue("MISSING_FIELD", "warning", f"Campo obbligatorio da confermare: {key}", key))
    if data.get("date"):
        try:
            date.fromisoformat(data["date"])
        except (TypeError, ValueError):
            issues.append(issue("BAD_DATE", "error", "La data deve essere AAAA-MM-GG", "date"))
    if data.get("recording_authorization") not in ("confirmed", "not_applicable", "unknown"):
        issues.append(issue("PRIVACY_RECORDING", "warning", "Indicare lo stato dell'autorizzazione/liceità della registrazione e del trattamento", "recording_authorization"))
    if data.get("used_recording") and data.get("recording_authorization") != "confirmed":
        issues.append(issue("PRIVACY_REVIEW", "error", "Registrazione utilizzata, ma verifica privacy non documentata", "recording_authorization"))
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        sources = []
        issues.append(issue("SOURCE_TYPE", "error", "sources deve essere una lista", "sources"))
    source_ids = [s.get("id") for s in sources if isinstance(s, dict) and s.get("id")]
    if len(source_ids) != len(set(source_ids)):
        issues.append(issue("SOURCE_DUPLICATE", "error", "ID fonti duplicati", "sources"))
    if not sources:
        issues.append(issue("SOURCE_MISSING", "warning", "Nessuna fonte documentale indicata", "sources"))
    attendees = data.get("attendees", [])
    if not isinstance(attendees, list):
        attendees = []
        issues.append(issue("ATTENDEES_TYPE", "error", "attendees deve essere una lista", "attendees"))
    identifiers = [a.get("id") for a in attendees if isinstance(a, dict)]
    if len(identifiers) != len(set(identifiers)) or any(not x for x in identifiers):
        issues.append(issue("ATTENDEES_ID", "error", "ID partecipanti mancanti o duplicati", "attendees"))
    present_rows = [a for a in attendees if isinstance(a, dict) and a.get("present") is True]
    present_ids = {a.get("id") for a in present_rows}
    n_present = len(present_rows)
    n_total = data.get("voters_total")
    if not isinstance(n_total, int) or isinstance(n_total, bool) or n_total <= 0:
        issues.append(issue("TOTAL_VOTERS", "warning", "Numero totale aventi diritto non indicato o non valido", "voters_total"))
        n_total = None
    elif n_present > n_total:
        issues.append(issue("EXCESS_HEADS", "error", "Presenti oltre il numero totale degli aventi diritto", "attendees"))
    total = Decimal(0)
    if kind == "condominio":
        try:
            total = decimal(data.get("total_millesimi", 1000), "total_millesimi")
        except ValueError:
            issues.append(issue("TOTAL_MILLESIMI", "error", "Totale millesimi numericamente non valido", "total_millesimi"))
    present_value = Decimal(0)
    attendee_milli = {}
    if kind == "condominio":
        if total <= 0:
            issues.append(issue("TOTAL_MILLESIMI", "error", "Totale millesimi deve essere positivo", "total_millesimi"))
        for a in attendees:
            if not isinstance(a, dict):
                issues.append(issue("ATTENDEE_SHAPE", "error", "Ogni partecipante deve essere oggetto JSON", "attendees"))
                continue
            key = a.get("id")
            try:
                share = decimal(a.get("millesimi"), f"millesimi {key}")
                if share < 0:
                    raise ValueError("Millesimi negativi")
                if key:
                    attendee_milli[key] = share
                if a.get("present"):
                    present_value += share
            except ValueError:
                issues.append(issue("INVALID_MILLESIMI", "error", f"Millesimi assenti o non validi per {key}", "attendees"))
        if present_value > total:
            issues.append(issue("EXCESS_MILLESIMI", "error", "Millesimi presenti superiori al totale edificio", "attendees"))
        # Non assumere che tutti gli aventi diritto siano nella lista: lista dei soli intervenuti ammessa.
    if kind == "cda":
        if any(a.get("represented_by") for a in attendees if isinstance(a, dict)):
            issues.append(issue("BOARD_PROXY", "error", "Nel CDA S.p.A. non è ammesso voto per rappresentanza (art. 2388 c.c.)", "attendees"))
        if data.get("company_type") != "spa":
            issues.append(issue("COMPANY_TYPE", "warning", "Le soglie base dell'art. 2388 sono riferite alla S.p.A.; verificare il tipo societario", "company_type"))
        if data.get("statute_reviewed") is not True:
            issues.append(issue("STATUTE", "warning", "Statuto non verificato: quorum e modalità possono cambiare", "statute_reviewed"))
    conv = data.get("convocation")
    if kind == "condominio" and conv not in (1, 2):
        issues.append(issue("CONVOCATION", "warning", "Indicare prima o seconda convocazione", "convocation"))
    if kind == "condominio" and data.get("all_entitled_notified") is not True:
        issues.append(issue("NOTICES", "warning", "Regolare convocazione di tutti gli aventi diritto da verificare", "all_entitled_notified"))
    items = data.get("agenda", [])
    if not isinstance(items, list):
        items = []
        issues.append(issue("AGENDA_TYPE", "error", "agenda deve essere una lista", "agenda"))
    for index, item in enumerate(items):
        path = f"agenda[{index}]"
        if not isinstance(item, dict):
            issues.append(issue("AGENDA_ITEM", "error", "Punto ODg non valido", path))
            continue
        if not item.get("subject"):
            issues.append(issue("SUBJECT", "warning", "Punto dell'ordine del giorno senza oggetto", path))
        if item.get("outcome") not in ("approvato", "respinto", "rinviato", "discusso", "non_determinato"):
            issues.append(issue("OUTCOME", "warning", "Esito non verificato o mancante", path))
        for sid in item.get("evidence", []):
            if sid not in source_ids:
                issues.append(issue("EVIDENCE_MISSING", "error", f"Fonte {sid!r} non trovata", path))
        if item.get("outcome") in ("approvato", "respinto") and not item.get("evidence"):
            issues.append(issue("DECISION_UNSOURCED", "warning", "Decisione senza riferimento a fonte", path))
        rule = item.get("quorum_rule", "manuale")
        if rule not in RULES:
            issues.append(issue("UNKNOWN_RULE", "error", "Regola di quorum non riconosciuta", path))
            rule = "manuale"
        raw_votes = item.get("votes", [])
        if not isinstance(raw_votes, list):
            raw_votes = []
            issues.append(issue("VOTES_TYPE", "error", "votes deve essere una lista", path))
        vote_map = {}
        for vote in raw_votes:
            if not isinstance(vote, dict):
                issues.append(issue("VOTE_SHAPE", "error", "Voto non valido", path))
                continue
            who, choice = vote.get("voter_id"), vote.get("choice")
            if who not in present_ids:
                issues.append(issue("VOTE_NONPRESENT", "error", f"Voto per {who!r} non presente", path))
            if who in vote_map:
                issues.append(issue("VOTE_DUPLICATE", "error", f"Doppio voto di {who!r}", path))
            if choice not in VOTES:
                issues.append(issue("VOTE_VALUE", "error", f"Esito voto non riconosciuto: {choice!r}", path))
            if who:
                vote_map[who] = choice
        if item.get("outcome") in ("approvato", "respinto") and set(vote_map) != present_ids:
            issues.append(issue("VOTES_INCOMPLETE", "warning", "Registrare il voto/astensione di ogni avente diritto presente", path))
        favors = [p for p, v in vote_map.items() if v == "favorevole"]
        favor_value = sum((attendee_milli.get(p, Decimal(0)) for p in favors), Decimal(0))
        calc = {"constituted": None, "favorable": None, "message": "Dati insufficienti"}
        if n_total is not None and not any(x["code"] in {"INVALID_MILLESIMI", "EXCESS_MILLESIMI", "ATTENDEES_ID", "EXCESS_HEADS"} for x in issues):
            vote_errors = any(x["level"] == "error" and x["path"] == path and x["code"].startswith("VOTE") for x in issues)
            if vote_errors:
                calc["message"] = "Votazione incoerente: risultati numerici sospesi"
            elif kind == "cda" and (data.get("company_type") != "spa" or data.get("statute_reviewed") is not True):
                calc["message"] = "Tipo societario/statuto non confermati: controllo CDA sospeso"
            elif item.get("outcome") in ("approvato", "respinto") and set(vote_map) != present_ids:
                calc["message"] = "Voti incompleti: soglie non valutabili"
            else:
                c, f, msg = _numeric_thresholds(kind, conv, total, present_value, n_total, n_present, len(favors), favor_value, rule)
                calc = {"constituted": c, "favorable": f, "message": msg}
                if c is False:
                    issues.append(issue("CONSTITUTION_THRESHOLD", "error", "Soglia numerica di costituzione non raggiunta", path))
                if f is False and item.get("outcome") == "approvato":
                    issues.append(issue("APPROVAL_THRESHOLD", "error", "Esito 'approvato' incompatibile con soglia numerica dichiarata", path))
                if f is True and item.get("outcome") == "respinto":
                    issues.append(issue("OUTCOME_CONFLICT", "warning", "Esito 'respinto' da verificare: voti superano la soglia dichiarata", path))
        results.append({"subject": item.get("subject", f"Punto {index + 1}"), "outcome": item.get("outcome", "non_determinato"), "rule": rule, "present_heads": n_present, "present_millesimi": str(present_value) if kind == "condominio" else None, "favorable_heads": len(favors), "favorable_millesimi": str(favor_value) if kind == "condominio" else None, **calc})
    for n, action in enumerate(data.get("actions", [])):
        if not isinstance(action, dict):
            issues.append(issue("ACTION_SHAPE", "error", "Attività non valida", f"actions[{n}]"))
            continue
        for key in ("task", "owner", "due_date"):
            if not action.get(key):
                issues.append(issue("ACTION_INCOMPLETE", "warning", f"Attività senza {key}", f"actions[{n}]"))
        for sid in action.get("evidence", []):
            if sid not in source_ids:
                issues.append(issue("ACTION_EVIDENCE", "error", f"Fonte attività {sid!r} inesistente", f"actions[{n}]"))
    status = "da_verificare" if issues or any(r["favorable"] is None for r in results) else "controlli_numerici_completati"
    return {"status": status, "issues": issues, "resolutions": results, "notice": "Controllo preliminare dei dati: non costituisce verifica legale né certificazione di validità."}
