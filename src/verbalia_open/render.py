"""Report e documenti bozze; nessuna approvazione automatica."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from .engine import assess


def safe(value):
    if value is None or value == "":
        return "[DA COMPLETARE]"
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def render_minutes(data: dict, report: dict | None = None) -> str:
    report = report or assess(data)
    kind = data.get("type", "riunione")
    lines = ["# VERBALE DI RIUNIONE — BOZZA DA VERIFICARE", "", f"**Tipologia:** {safe(kind)}  ", f"**Oggetto:** {safe(data.get('title'))}  ", f"**Data:** {safe(data.get('date'))}  ", f"**Ora:** {safe(data.get('start_time'))} – {safe(data.get('end_time'))}  ", f"**Luogo / modalità:** {safe(data.get('location'))}  ", f"**Presiede:** {safe(data.get('chair'))}  ", f"**Segretario verbalizzante:** {safe(data.get('secretary'))}", ""]
    if kind == "condominio":
        lines += [f"**Convocazione:** {safe(data.get('convocation'))}  ", f"**Aventi diritto complessivi:** {safe(data.get('voters_total'))}  ", ""]
    lines += ["## Presenze e rappresentanze", ""]
    attendees = data.get("attendees", [])
    if attendees:
        lines += ["| Nominativo | Presente | Rappresentante | Millesimi* |", "|---|---|---|---:|"]
        for a in attendees:
            lines.append(f"| {safe(a.get('name'))} | {'Sì' if a.get('present') else 'No'} | {safe(a.get('represented_by') or '—')} | {safe(a.get('millesimi') if kind == 'condominio' else '—')} |")
        lines += ["", "*Quote riportate come dichiarate nella scheda; verificare deleghe, tabelle e titolarità.*", ""]
    else:
        lines += ["[PRESENZE DA COMPLETARE]", ""]
    lines += ["## Svolgimento e punti all'ordine del giorno", ""]
    for i, item in enumerate(data.get("agenda", []), 1):
        lines += [f"### {i}. {safe(item.get('subject'))}", "", f"**Discussione sintetica:** {safe(item.get('discussion'))}", "", f"**Proposta/testo della deliberazione:** {safe(item.get('resolution_text'))}", "", f"**Esito dichiarato:** {safe(item.get('outcome'))}  ", f"**Fonti dichiarate:** {safe(', '.join(item.get('evidence', [])) if item.get('evidence') else None)}", ""]
        if item.get("votes"):
            lines += ["| Votante | Voto |", "|---|---|"]
            for vote in item["votes"]:
                lines.append(f"| {safe(vote.get('voter_id'))} | {safe(vote.get('choice'))} |")
            lines.append("")
        if i <= len(report["resolutions"]):
            r = report["resolutions"][i - 1]
            lines += [f"**Controllo preliminare:** {safe(r.get('message'))}; costituzione={safe(r.get('constituted'))}, soglia approvazione={safe(r.get('favorable'))}.", ""]
    lines += ["## Incarichi, responsabili e scadenze", ""]
    if data.get("actions"):
        lines += ["| Attività | Responsabile | Scadenza | Fonte |", "|---|---|---|---|"]
        for a in data["actions"]:
            lines.append(f"| {safe(a.get('task'))} | {safe(a.get('owner'))} | {safe(a.get('due_date'))} | {safe(', '.join(a.get('evidence', [])) if a.get('evidence') else None)} |")
    else:
        lines.append("Nessuna attività confermata.")
    lines += ["", "## Allegati e fonti", ""]
    for s in data.get("sources", []):
        lines.append(f"- {safe(s.get('id'))}: {safe(s.get('description'))} ({safe(s.get('type'))})")
    if not data.get("sources"):
        lines.append("[NESSUNA FONTE INDICATA]")
    lines += ["", "## Rilievi da risolvere prima della firma", ""]
    if report["issues"]:
        for item in report["issues"]:
            lines.append(f"- **{safe(item['level']).upper()} / {safe(item['code'])}:** {safe(item['message'])}")
    else:
        lines.append("Nessuna incongruenza rilevata dai controlli implementati; resta necessaria verifica professionale.")
    lines += ["", f"**Chiusura della riunione:** {safe(data.get('end_time'))}", "", "**Presidente:** __________________  **Segretario:** __________________", "", "> Documento generato come bozza; approvazione, verifica normativa, firma e distribuzione restano sotto responsabilità umana.", ""]
    return "\n".join(lines)


def actions_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["task", "owner", "due_date", "status", "evidence"])
    for item in data.get("actions", []):
        writer.writerow([item.get("task", ""), item.get("owner", ""), item.get("due_date", ""), item.get("status", "da_avviare"), ";".join(item.get("evidence", []))])
    return output.getvalue()


def audit_json(data: dict, report: dict) -> str:
    audit = {"schema_version": "0.2", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "meeting_id": data.get("id"), "checks": report, "approval_state": "NOT_APPROVED", "review_required": True}
    return json.dumps(audit, indent=2, ensure_ascii=False)


def render_summary(data: dict) -> str:
    rows = ["# Sintesi operativa — non sostituisce il verbale", "", f"**Riunione:** {safe(data.get('title'))} — {safe(data.get('date'))}", "", "## Decisioni dichiarate", ""]
    rows.extend(f"- {safe(a.get('subject'))}: **{safe(a.get('outcome'))}** — {safe(a.get('resolution_text'))}" for a in data.get("agenda", []))
    rows += ["", "## Prossime attività", ""]
    rows.extend(f"- {safe(a.get('owner'))}: {safe(a.get('task'))} (entro {safe(a.get('due_date'))})" for a in data.get("actions", []))
    return "\n".join(rows) + "\n"
