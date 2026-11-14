"""Signed real-time transcript ingestion and human-review snapshots."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

MAX_REQUEST_BYTES = 1_000_000


def verify_recall_signature(secret: str, headers, body: bytes, *, now=None, max_skew=300) -> str:
    if not secret.startswith("whsec_"):
        raise ValueError("Segreto webhook assente o non valido")
    def get(name):
        return headers.get(name, headers.get(name.title(), ""))
    msg_id = get("webhook-id") or get("svix-id")
    ts = get("webhook-timestamp") or get("svix-timestamp")
    signatures = get("webhook-signature") or get("svix-signature")
    if not msg_id or not ts or not signatures:
        raise ValueError("Firma webhook mancante")
    try:
        timestamp = int(ts)
        if abs((now if now is not None else time.time()) - timestamp) > max_skew:
            raise ValueError("Timestamp scaduto")
        key = base64.b64decode(secret[6:], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Firma webhook non valida") from exc
    message = msg_id.encode() + b"." + ts.encode() + b"." + body
    expected = hmac.new(key, message, hashlib.sha256).digest()
    for element in signatures.split():
        prefix, _, encoded = element.partition(",")
        if prefix != "v1" or not encoded:
            continue
        try:
            if hmac.compare_digest(expected, base64.b64decode(encoded, validate=True)):
                return msg_id
        except ValueError:
            continue
    raise ValueError("Firma webhook errata")


def normalize_event(payload: dict) -> dict | None:
    if not isinstance(payload, dict):
        raise ValueError("Formato evento non valido")
    if payload.get("event") != "transcript.data":
        return None
    envelope = payload.get("data") or {}
    details = envelope.get("data") or {}
    words = details.get("words") or []
    if not isinstance(words, list):
        raise ValueError("Formato parole non valido")
    utterance = " ".join(str(w.get("text", "")).strip() for w in words if isinstance(w, dict)).strip()
    if not utterance:
        return None
    first = next((w for w in words if isinstance(w, dict)), {})
    sec = (first.get("start_timestamp") or {}).get("relative")
    participant = details.get("participant") or {}
    bot = envelope.get("bot") or {}
    return {"bot_id": str(bot.get("id") or ""), "speaker": str(participant.get("name") or "Interlocutore non identificato"),
            "speaker_id": participant.get("id"), "second": sec, "text": utterance}


def append_event(path: Path, event: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)


def transcript_markdown(entries: list[dict], *, bot_id: str | None = None) -> str:
    lines = ["# Verbalia Live — trascrizione provvisoria", "", "Fonte: eventi di trascrizione della riunione. Nomi e testo da verificare.",
             "**Non è un verbale approvato e nessuna frase costituisce automaticamente delibera.**", ""]
    count = 0
    for entry in entries:
        if bot_id and entry.get("bot_id") != bot_id:
            continue
        count += 1
        seconds = entry.get("second")
        stamp = "?" if not isinstance(seconds, (int, float)) or seconds < 0 else f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
        speaker = str(entry.get("speaker", "?"))
        utterance = str(entry.get("text", "")).replace("\n", " ")
        lines.append(f"- **[TR-{count:04d} · {stamp}] {speaker}:** {utterance}")
    if not count:
        lines.append("_[Nessun intervento ricevuto]_ ")
    lines += ["", "## Frasi da rivedere manualmente", "", "Segnalazioni lessicali, non decisioni accertate:", ""]
    triggers = re.compile(r"\b(deliberat[oaie]|deliberare|approvat[oaie]|approvare|votazion[ei]|incaric[oa]|scadenz[ae]|entro il|respint[oaie]|contrari|astenut[ioa])\b", re.I)
    highlights = [e for e in entries if (not bot_id or e.get("bot_id") == bot_id) and triggers.search(str(e.get("text", "")))]
    for entry in highlights:
        lines.append(f"- [DA VERIFICARE] {entry.get('speaker', '?')}: {entry.get('text', '')}")
    if not highlights:
        lines.append("- Nessuna frase selezionata automaticamente; leggere comunque tutta la trascrizione.")
    return "\n".join(lines).rstrip() + "\n"


def build_snapshot(path: Path, bot_id: str | None = None) -> str:
    entries = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"Evento alla riga {number} non valido")
        entries.append(obj)
    return transcript_markdown(entries, bot_id=bot_id)


def make_webhook_handler(secret: str, out: Path, *, allowed_bot_ids: frozenset[str]):
    if not allowed_bot_ids:
        raise ValueError("Indicare almeno un UUID bot autorizzato: --bot-id")
    seen_ids: set[str] = set()
    append_lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/recall/events":
                self.send_error(404)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 1 or size > MAX_REQUEST_BYTES:
                    self.send_error(413)
                    return
                body = self.rfile.read(size)
                msg_id = verify_recall_signature(secret, self.headers, body)
                payload = json.loads(body)
                event = normalize_event(payload)
                if event and event["bot_id"] not in allowed_bot_ids:
                    self.send_error(403)
                    return
                if event is not None:
                    with append_lock:
                        if msg_id not in seen_ids:
                            append_event(out, event)
                            seen_ids.add(msg_id)
                self.send_response(204)
                self.end_headers()
            except OSError:
                self.send_error(503, "Salvataggio temporaneamente non disponibile")
            except (ValueError, AttributeError):
                self.send_error(400, "Evento non valido")

        def log_message(self, format, *args):
            # No raw transcript content or public URL logged.
            pass

    return Handler


def serve_webhooks(*, host: str, port: int, out: Path, bot_ids: list[str], secret: str | None = None):
    from .live import validate_bot_id
    secret = secret or os.environ.get("RECALL_WORKSPACE_VERIFICATION_SECRET", "")
    ids = frozenset(validate_bot_id(x) for x in bot_ids)
    if not secret.startswith("whsec_"):
        raise ValueError("Impostare RECALL_WORKSPACE_VERIFICATION_SECRET=whsec_...")
    with ThreadingHTTPServer((host, port), make_webhook_handler(secret, out, allowed_bot_ids=ids)) as server:
        print(f"Ricevitore attivo su {host}:{port}/recall/events (richiesto proxy HTTPS pubblico)")
        server.serve_forever()
