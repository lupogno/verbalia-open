"""CLI locale per verbali, audit e output Word/PDF."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .engine import KINDS, assess
from .live import BOT_NAME
from .render import render_minutes, render_summary, actions_csv, audit_json


def load(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Il file deve contenere un oggetto JSON")
    return data


def save(path: str | Path, content: str):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def create_bundle(data: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    report = assess(data)
    output = {"minutes": save(out / "verbale-bozza.md", render_minutes(data, report)),
              "summary": save(out / "sintesi.md", render_summary(data)),
              "audit": save(out / "audit.json", audit_json(data, report)),
              "actions": save(out / "azioni.csv", actions_csv(data))}
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(prog="verbalia", description="Verbalia Open — skill e verifiche per verbali")
    parser.add_argument("--version", action="version", version=__version__)
    cmds = parser.add_subparsers(dest="command", required=True)
    p_validate = cmds.add_parser("validate", help="Controlla un JSON senza eseguire chiamate esterne")
    p_validate.add_argument("input")
    p_validate.add_argument("--json", action="store_true")
    p_render = cmds.add_parser("render", help="Produce verbale Markdown, opzionalmente DOCX o PDF")
    p_render.add_argument("input")
    p_render.add_argument("--format", choices=["md", "docx", "pdf"], default="md")
    p_render.add_argument("--out", required=True)
    p_bundle = cmds.add_parser("bundle", help="Verbale, riepilogo, audit e CSV azioni")
    p_bundle.add_argument("input")
    p_bundle.add_argument("--out", required=True)
    p_draft = cmds.add_parser("ai-draft", help="Crea bozza JSON da appunti: invio a provider esterno")
    p_draft.add_argument("notes")
    p_draft.add_argument("--type", required=True, choices=sorted(KINDS))
    p_draft.add_argument("--model", required=True)
    p_draft.add_argument("--out", required=True)
    p_draft.add_argument("--allow-external-processing", action="store_true")
    p_review = cmds.add_parser("ai-review", help="Controlla una bozza rispetto agli appunti usando AI esterna")
    p_review.add_argument("input")
    p_review.add_argument("--notes", required=True)
    p_review.add_argument("--model", required=True)
    p_review.add_argument("--out", required=True)
    p_review.add_argument("--allow-external-processing", action="store_true")
    p_transcribe = cmds.add_parser("transcribe", help="Trascrive audio con provider esterno (opt-in)")
    p_transcribe.add_argument("audio")
    p_transcribe.add_argument("--model", default="gpt-4o-transcribe")
    p_transcribe.add_argument("--out", required=True)
    p_transcribe.add_argument("--allow-external-processing", action="store_true")
    p_live = cmds.add_parser("live", help="Agente dichiarato in videocall tramite Recall.ai (opt-in)")
    live_cmds = p_live.add_subparsers(dest="live_command", required=True)
    p_join = live_cmds.add_parser("join", help="Invia un assistente visibile senza avviare la trascrizione")
    p_join.add_argument("meeting_url")
    p_join.add_argument("--name", default=BOT_NAME, help="Etichetta aggiuntiva dopo il nome dell'assistente")
    p_join.add_argument("--join-at", help="Data ISO8601 con fuso (per riunioni future)")
    p_join.add_argument("--allow-external-processing", action="store_true")
    p_join.add_argument("--participants-informed", action="store_true", help="Confermo di aver informato i partecipanti dell'invito")
    p_start = live_cmds.add_parser("start", help="Avvia la trascrizione dopo la conferma dell'operatore")
    p_start.add_argument("bot_id")
    p_start.add_argument("--language", choices=["it", "en", "auto"], default="it")
    p_start.add_argument("--captions", action="store_true", help="Usa sottotitoli della piattaforma se disponibili")
    p_start.add_argument("--webhook-url", help="Endpoint HTTPS pubblico terminante in /recall/events")
    p_start.add_argument("--retention-hours", type=int, default=24, help="Ore di conservazione dei media su Recall (default 24)")
    p_start.add_argument("--allow-external-processing", action="store_true")
    p_start.add_argument("--participants-informed", action="store_true", help="Confermo informativa, base giuridica ed eventuali consensi necessari per trascrivere")
    p_stop = live_cmds.add_parser("stop", help="Ferma l'acquisizione per la trascrizione")
    p_stop.add_argument("bot_id")
    p_status = live_cmds.add_parser("status", help="Leggi stato di un bot già avviato")
    p_status.add_argument("bot_id")
    p_leave = live_cmds.add_parser("leave", help="Rimuovi il bot dalla videocall")
    p_leave.add_argument("bot_id")
    p_leave.add_argument("--confirm-leave", action="store_true")
    p_fetch = live_cmds.add_parser("transcript", help="Scarica la trascrizione dopo transcript.done")
    p_fetch.add_argument("bot_id")
    p_fetch.add_argument("--out", required=True)
    p_events = live_cmds.add_parser("serve", help="Ricevi via webhook HTTPS (tramite proxy) eventi live firmati")
    p_events.add_argument("--host", default="127.0.0.1")
    p_events.add_argument("--port", type=int, default=8787)
    p_events.add_argument("--bot-id", action="append", required=True)
    p_events.add_argument("--out", default="private/live-events.jsonl")
    p_snap = live_cmds.add_parser("snapshot", help="Compila la trascrizione live ricevuta senza AI")
    p_snap.add_argument("--events", required=True)
    p_snap.add_argument("--bot-id")
    p_snap.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "live":
            from .live import RecallClient, new_bot_payload, new_recording_config, status_summary
            from .live_events import build_snapshot, serve_webhooks, transcript_markdown
            if args.live_command == "snapshot":
                save(args.out, build_snapshot(Path(args.events), args.bot_id))
                print(f"Bozza live: {args.out}")
                return 0
            if args.live_command == "serve":
                serve_webhooks(host=args.host, port=args.port, out=Path(args.out), bot_ids=args.bot_id)
                return 0
            if args.live_command in {"join", "start"}:
                if not args.allow_external_processing or not args.participants_informed:
                    parser.error("Confermare --allow-external-processing e --participants-informed prima di proseguire")
            if args.live_command == "join":
                payload = new_bot_payload(args.meeting_url, name=args.name, join_at=args.join_at)
                bot = RecallClient().join(payload)
                print(json.dumps({"bot_id": bot.get("id"), "message": "Ingresso richiesto senza trascrizione. Verificare stato e sala d'attesa."}, ensure_ascii=False))
                return 0
            if args.live_command == "start":
                config = new_recording_config(language=args.language, webhook_url=args.webhook_url,
                                              captions=args.captions, retention_hours=args.retention_hours)
                RecallClient().start_recording(args.bot_id, config)
                print("Avvio trascrizione richiesto. Controllare lo stato del bot.")
                return 0
            if args.live_command == "stop":
                RecallClient().stop_recording(args.bot_id)
                print("Richiesta di arresto acquisizione inviata.")
                return 0
            if args.live_command == "leave":
                if not args.confirm_leave:
                    parser.error("Per uscire aggiungere --confirm-leave")
                RecallClient().leave(args.bot_id)
                print("Richiesta di uscita inviata.")
                return 0
            client = RecallClient()
            if args.live_command == "status":
                print(json.dumps(status_summary(client.status(args.bot_id)), ensure_ascii=False, indent=2))
                return 0
            if args.live_command == "transcript":
                entries = client.get_transcript(args.bot_id)
                normalized = []
                for item in entries:
                    words = item.get("words") or []
                    speaker = item.get("participant") or {}
                    first = words[0] if words else {}
                    normalized.append({"bot_id": args.bot_id, "speaker": speaker.get("name") or "Interlocutore non identificato",
                                       "second": (first.get("start_timestamp") or {}).get("relative"),
                                       "text": " ".join(str(w.get("text", "")) for w in words).strip()})
                save(args.out, transcript_markdown(normalized, bot_id=args.bot_id))
                print(f"Trascrizione salvata: {args.out}")
                return 0
        if args.command in {"ai-draft", "ai-review", "transcribe"}:
            if not args.allow_external_processing:
                parser.error("Elaborazione esterna disabilitata: serve --allow-external-processing dopo una verifica privacy")
            from . import ai
            if args.command == "transcribe":
                path = Path(args.audio)
                if not path.is_file():
                    raise ValueError(f"Audio non trovato: {path}")
                save(args.out, ai.transcribe(path, args.model))
            elif args.command == "ai-draft":
                notes = Path(args.notes).read_text(encoding="utf-8")
                draft = ai.draft_from_notes(notes, args.type, args.model)
                save(args.out, json.dumps(draft, ensure_ascii=False, indent=2))
                print("Bozza da revisionare. Esegui 'verbalia validate' prima dell'uso.")
            else:
                data = load(args.input)
                notes = Path(args.notes).read_text(encoding="utf-8")
                save(args.out, ai.review_draft(data, notes, args.model))
            print(f"Creato {args.out}")
            return 0
        data = load(args.input)
        report = assess(data)
        if args.command == "validate":
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(f"Controllo: {report['status']}; rilievi: {len(report['issues'])}")
                for x in report["issues"]:
                    print(f"  {x['level']}: {x['code']} — {x['message']}")
            return 1 if any(x["level"] == "error" for x in report["issues"]) else 0
        if args.command == "bundle":
            files = create_bundle(data, Path(args.out))
            for name, path in files.items():
                print(f"{name}: {path}")
            return 0
        if args.command == "render":
            content = render_minutes(data, report)
            target = Path(args.out)
            target.parent.mkdir(parents=True, exist_ok=True)
            if args.format == "md":
                save(target, content)
            elif args.format == "docx":
                from .exporters import markdown_to_docx
                markdown_to_docx(content, target)
            else:
                from .exporters import markdown_to_pdf
                markdown_to_pdf(content, target)
            print(f"Bozza creata: {target}")
            return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 2
    return 2
