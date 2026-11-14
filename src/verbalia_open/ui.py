"""Interfaccia locale Streamlit: verbali offline e join live solo su conferma."""
from __future__ import annotations
import json
from verbalia_open.engine import assess
from verbalia_open.render import render_minutes, render_summary, actions_csv


def _minutes_tab(st):
    st.warning("Per le prove usa dati fittizi. Controlla la sicurezza dell'hosting prima di caricare dati reali.")
    uploaded = st.file_uploader("Carica riunione JSON", type=["json"])
    if not uploaded:
        st.info("Inizia con examples/condominio.json e la guida README")
        return
    try:
        data = json.loads(uploaded.getvalue().decode("utf-8"))
        report = assess(data)
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        st.error(f"Dati non validi: {exc}")
        return
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Verbale")
        st.markdown(render_minutes(data, report))
    with right:
        st.subheader("Audit")
        st.metric("Rilievi", len(report["issues"]))
        st.json(report)
    st.download_button("Scarica verbale Markdown", data=render_minutes(data, report), file_name="verbale-bozza.md", mime="text/markdown")
    st.download_button("Scarica azioni CSV", data=actions_csv(data), file_name="azioni.csv", mime="text/csv")
    st.download_button("Scarica riepilogo", data=render_summary(data), file_name="sintesi.md", mime="text/markdown")


def _live_tab(st):
    from verbalia_open.live import BOT_NAME, RecallClient, new_bot_payload, new_recording_config, status_summary
    from verbalia_open.live_events import build_snapshot
    from pathlib import Path
    st.subheader("Verbalia Live — assistente partecipante")
    st.info("L'assistente entra con un nome riconoscibile. L'host può ammetterlo dalla sala d'attesa e autorizzare la trascrizione dopo l'ingresso. Serve un account Recall.ai.")
    with st.form("live_join"):
        url = st.text_input("Link di riunione (Meet, Zoom, Teams o Webex)", placeholder="https://meet.google.com/abc-defg-hij")
        name = st.text_input("Etichetta aggiuntiva", placeholder=BOT_NAME)
        informed = st.checkbox("Ho informato i partecipanti dell'invito")
        external = st.checkbox("Autorizzo l'invio del link a Recall.ai")
        join = st.form_submit_button("Invita l'assistente")
    if join and not (informed and external):
        st.warning("Conferma entrambe le dichiarazioni per inviare l'invito.")
    elif join:
        try:
            payload = new_bot_payload(url, name=name or BOT_NAME)
            bot = RecallClient().join(payload)
            st.session_state["verbalia_live_bot"] = bot["id"]
            st.success("Invito inviato senza avviare la trascrizione. Verifica lo stato dell'assistente.")
        except (RuntimeError, ValueError, KeyError) as exc:
            st.error(f"Impossibile inviare il bot: {exc}")
    bot_id = st.text_input("ID bot da monitorare o allontanare", value=st.session_state.get("verbalia_live_bot", ""))
    with st.form("live_start", clear_on_submit=True):
        lang = st.selectbox("Lingua del parlato", options=["it", "auto", "en"])
        captions = st.checkbox("Usa i sottotitoli della piattaforma se disponibili")
        webhook = st.text_input("Endpoint HTTPS per gli eventi live (facoltativo)", placeholder="https://api.example.org/recall/events")
        retention = st.number_input("Conservazione su Recall in ore", min_value=1, value=24, step=1)
        privacy = st.checkbox("Ho informato i presenti e verificato la base giuridica e gli eventuali consensi")
        authorize = st.checkbox("Autorizzo la trascrizione tramite Recall.ai")
        start = st.form_submit_button("Avvia trascrizione", disabled=not bot_id)
    if start and not (privacy and authorize):
        st.warning("Conferma entrambe le dichiarazioni prima di avviare la trascrizione.")
    elif start:
        try:
            config = new_recording_config(language=lang, captions=captions, webhook_url=webhook or None,
                                          retention_hours=retention)
            RecallClient().start_recording(bot_id, config)
            st.success("Avvio trascrizione richiesto. Verifica lo stato dell'assistente.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

    if st.button("Ferma trascrizione", disabled=not bot_id):
        try:
            RecallClient().stop_recording(bot_id)
            st.success("Richiesta di arresto acquisizione inviata.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Verifica stato", disabled=not bot_id):
            try:
                st.json(status_summary(RecallClient().status(bot_id)))
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
    with col2:
        if st.button("Rimuovi dalla riunione", disabled=not bot_id):
            try:
                RecallClient().leave(bot_id)
                st.success("Richiesta di uscita inviata.")
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
    st.divider()
    st.caption("Per leggere gli interventi durante la riunione, configura il ricevitore webhook HTTPS prima di avviare la trascrizione.")
    events_path = st.text_input("File eventi ricevuti localmente", value="private/live-events.jsonl")
    if st.button("Mostra trascrizione live", disabled=not bot_id):
        try:
            content = build_snapshot(Path(events_path), bot_id)
            st.text(content)
            st.download_button("Scarica trascrizione provvisoria", content, file_name="trascrizione-live.md")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            st.warning(f"Nessuna trascrizione disponibile: {exc}")


def main():
    try:
        import streamlit as st
    except ImportError as exc:
        raise SystemExit("Installa UI: pip install '.[ui]'") from exc
    st.set_page_config(page_title="Verbalia Open", page_icon="📝", layout="wide")
    st.title("Verbalia Open")
    st.caption("Verbali verificabili; nessuna validità legale automatica")
    minutes, live = st.tabs(["Verbali e audit", "Meeting Live"])
    with minutes:
        _minutes_tab(st)
    with live:
        _live_tab(st)


if __name__ == "__main__":
    main()
