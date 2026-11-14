"""Opt-in visible meeting participant integration; Recall.ai v1.11 REST.

This module does not join a call on import and never exposes secrets in output.
"""
from __future__ import annotations

import json
import os
import ipaddress
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit
from uuid import UUID
from . import __version__

REGIONS = frozenset({"eu-central-1", "us-east-1", "us-west-2", "ap-northeast-1"})
BOT_NAME = "Verbalia AI - Assistente verbalizzante"
# Specific hosts only: protect operators against pasting arbitrary URLs with secrets.
HOSTS = frozenset({"meet.google.com", "zoom.us", "www.zoom.us", "teams.microsoft.com", "teams.live.com", "webex.com", "www.webex.com"})


def validate_meeting_url(url: str) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        raise ValueError("Il link deve essere HTTPS, senza credenziali nel dominio o porta personalizzata")
    if not (host in HOSTS or host.endswith(".zoom.us") or host.endswith(".webex.com")):
        raise ValueError("Piattaforma non supportata: Google Meet, Zoom, Teams o Webex")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Inserire il link specifico della riunione")
    if len(url) > 4096:
        raise ValueError("Link troppo lungo")
    return url


def validate_webhook_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port:
        raise ValueError("Il webhook deve essere un HTTPS pubblico senza credenziali o porte speciali")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("Il webhook deve essere pubblicamente raggiungibile")
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            raise ValueError("Webhook su indirizzo IP non pubblico")
    except ValueError as exc:
        if "non pubblico" in str(exc):
            raise
    if parsed.query or parsed.fragment:
        raise ValueError("Non includere token o query nel link del webhook")
    if not parsed.path.endswith("/recall/events"):
        raise ValueError("URL del webhook deve terminare in /recall/events")
    return url


def validate_bot_id(bot_id: str) -> str:
    try:
        return str(UUID(bot_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("Bot ID non valido (richiesto UUID)") from exc


def new_bot_payload(meeting_url: str, *, name: str = BOT_NAME, join_at: str | None = None) -> dict:
    validate_meeting_url(meeting_url)
    if name != BOT_NAME:
        name = f"{BOT_NAME} | {name}"
    if len(name) > 100 or not name.isprintable():
        raise ValueError("Nome dell'assistente non valido")
    result = {"meeting_url": meeting_url, "bot_name": name, "recording_config": None}
    if join_at:
        try:
            when = datetime.fromisoformat(join_at.replace("Z", "+00:00"))
            if when.tzinfo is None or when.utcoffset() is None:
                raise ValueError()
        except ValueError as exc:
            raise ValueError("join-at deve essere ISO8601 con fuso orario") from exc
        result["join_at"] = join_at
    return result


def new_recording_config(*, language: str = "it", webhook_url: str | None = None,
                         captions: bool = False, retention_hours: int = 24) -> dict:
    if type(retention_hours) is not int or retention_hours < 1:
        raise ValueError("Conservazione Recall: indicare un numero intero positivo di ore")
    if captions:
        transcript = {"provider": {"meeting_captions": {}}}
    elif language == "en":
        transcript = {"provider": {"recallai_streaming": {"mode": "prioritize_low_latency", "language_code": "en"}},
                      "diarization": {"use_separate_streams_when_available": True}}
    else:
        if language not in {"it", "auto"}:
            raise ValueError("Lingua non supportata: usa it, auto oppure en")
        transcript = {"provider": {"recallai_streaming": {"mode": "prioritize_accuracy", "language_code": language}},
                      "diarization": {"use_separate_streams_when_available": True}}
    recording = {
        "transcript": transcript,
        "video_mixed_mp4": None,
        "participant_events": None,
        "meeting_metadata": None,
        "retention": {"type": "timed", "hours": retention_hours},
    }
    if webhook_url:
        recording["realtime_endpoints"] = [{"type": "webhook", "url": validate_webhook_url(webhook_url), "events": ["transcript.data"]}]
    return recording


class RecallClient:
    def __init__(self, *, api_key: str | None = None, region: str | None = None, opener=None):
        self.region = region or os.environ.get("RECALL_REGION", "eu-central-1")
        if self.region not in REGIONS:
            raise ValueError("RECALL_REGION non riconosciuta")
        self.api_key = api_key or os.environ.get("RECALL_API_KEY")
        if not self.api_key:
            raise ValueError("Impostare RECALL_API_KEY nell'ambiente (mai nel repository)")
        self.base = f"https://{self.region}.recall.ai/api/v1/bot/"
        self.opener = opener or urllib.request.urlopen

    def _call(self, method: str, endpoint: str, payload: dict | None = None):
        raw = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(self.base + endpoint, data=raw, method=method, headers={
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"VerbaliaOpen/{__version__}",
        })
        try:
            with self.opener(req, timeout=30) as response:
                blob = response.read(4_000_000)
                return json.loads(blob) if blob.strip() else {}
        except urllib.error.HTTPError as exc:
            # Provider errors can contain meeting links and other private data; do not echo response bodies.
            raise RuntimeError(f"Recall API: HTTP {exc.code}; controllare configurazione e autorizzazioni") from None
        except urllib.error.URLError as exc:
            raise RuntimeError("Recall API: connessione non disponibile") from exc

    def join(self, payload: dict):
        return self._call("POST", "", payload)

    def status(self, bot_id: str):
        return self._call("GET", f"{validate_bot_id(bot_id)}/")

    def leave(self, bot_id: str):
        return self._call("POST", f"{validate_bot_id(bot_id)}/leave_call/", {})

    def start_recording(self, bot_id: str, config: dict):
        return self._call("POST", f"{validate_bot_id(bot_id)}/start_recording/", config)

    def stop_recording(self, bot_id: str):
        return self._call("POST", f"{validate_bot_id(bot_id)}/stop_recording/", {})

    def get_transcript(self, bot_id: str):
        bot = self.status(bot_id)
        recordings = bot.get("recordings") or []
        link = None
        for recording in reversed(recordings):
            shortcut = (recording.get("media_shortcuts") or {}).get("transcript") or {}
            link = (shortcut.get("data") or {}).get("download_url")
            if link:
                break
        if not link:
            raise ValueError("Trascrizione non ancora disponibile: attendere transcript.done")
        parsed = urlsplit(link)
        # Presigned URL must be supplied by the trusted API, HTTPS and no inline credentials.
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("URL di download non sicuro")
        req = urllib.request.Request(link, headers={"Accept": "application/json", "User-Agent": f"VerbaliaOpen/{__version__}"})
        try:
            with self.opener(req, timeout=30) as response:
                content = response.read(25_000_000)
            transcript = json.loads(content)
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RuntimeError("Trascrizione non scaricabile") from exc
        if not isinstance(transcript, list):
            raise ValueError("Formato trascrizione imprevisto")
        return transcript


def status_summary(data: dict) -> dict:
    events = data.get("status_changes") or []
    latest = events[-1] if events and isinstance(events[-1], dict) else {}
    return {"bot_id": data.get("id"), "status": (latest.get("code") or data.get("status") or "sconosciuto"),
            "recordings": len(data.get("recordings") or [])}
