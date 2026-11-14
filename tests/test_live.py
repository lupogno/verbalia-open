"""Offline, mocked tests: NEVER join an actual external meeting."""
import base64
import hashlib
import hmac
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import time
from unittest.mock import patch
from uuid import uuid4
from verbalia_open.cli import main
from verbalia_open.live import RecallClient, new_bot_payload, new_recording_config, status_summary, validate_meeting_url
from verbalia_open.live_events import verify_recall_signature, normalize_event, transcript_markdown, append_event, build_snapshot, make_webhook_handler

BOT = str(uuid4())


class FakeResponse:
    def __init__(self, obj):
        self.raw = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, n=-1):
        return self.raw[:n]


class TestLive(unittest.TestCase):
    def test_only_meeting_provider_urls(self):
        self.assertEqual(validate_meeting_url('https://meet.google.com/abc-defg-hij'), 'https://meet.google.com/abc-defg-hij')
        self.assertEqual(validate_meeting_url('https://company.zoom.us/j/123?pwd=example'), 'https://company.zoom.us/j/123?pwd=example')
        for url in ['http://meet.google.com/a', 'https://evil.example/a', 'https://meet.google.com@evil.example/a', 'https://localhost/a', 'https://meet.google.com/', 'https://meet.google.com:8080/a']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_meeting_url(url)

    def test_language_latency_and_video_disabled(self):
        config = new_recording_config(language='it', webhook_url='https://api.example.org/recall/events')
        self.assertIsNone(config['video_mixed_mp4'])
        self.assertIsNone(config['participant_events'])
        self.assertIsNone(config['meeting_metadata'])
        self.assertEqual(config['retention'], {'type': 'timed', 'hours': 24})
        self.assertEqual(config['transcript']['provider']['recallai_streaming']['mode'], 'prioritize_accuracy')
        self.assertEqual(config['realtime_endpoints'][0]['events'], ['transcript.data'])
        y = new_recording_config(language='en')
        self.assertEqual(y['transcript']['provider']['recallai_streaming']['mode'], 'prioritize_low_latency')
        z = new_recording_config(captions=True)
        self.assertEqual(z['transcript']['provider'], {'meeting_captions': {}})
        with self.assertRaises(ValueError):
            new_recording_config(webhook_url='http://localhost:8787/recall/events')
        with self.assertRaises(ValueError):
            new_recording_config(retention_hours=0)
        with self.assertRaises(ValueError):
            new_bot_payload('https://zoom.us/j/123', join_at='2026-12-01T15:00:00')

    def test_scheduled_join_has_no_capture_and_keeps_disclosed_identity(self):
        payload = new_bot_payload('https://zoom.us/j/123', name='Assemblea', join_at='2026-12-01T15:00:00+01:00')
        self.assertIsNone(payload['recording_config'])
        self.assertEqual(payload['bot_name'], 'Verbalia AI - Assistente verbalizzante | Assemblea')
        self.assertEqual(payload['join_at'], '2026-12-01T15:00:00+01:00')

    def test_client_post_and_status_mocked(self):
        calls = []
        def opener(req, timeout):
            calls.append(req)
            return FakeResponse({'id': BOT, 'status_changes': [{'code':'in_waiting_room'}]})
        client = RecallClient(api_key='TEST_SECRET', opener=opener)
        bot = client.join(new_bot_payload('https://zoom.us/j/123'))
        self.assertEqual(bot['id'], BOT)
        self.assertEqual(calls[0].get_method(), 'POST')
        self.assertEqual(json.loads(calls[0].data)['bot_name'], 'Verbalia AI - Assistente verbalizzante')
        self.assertIsNone(json.loads(calls[0].data)['recording_config'])
        self.assertEqual(calls[0].get_header('Authorization'), 'TEST_SECRET')
        report = status_summary(client.status(BOT))
        self.assertEqual(report['status'], 'in_waiting_room')
        client.leave(BOT)
        self.assertIn('/leave_call/', calls[-1].full_url)

    def test_join_refuses_without_approval(self):
        with patch('verbalia_open.live.RecallClient') as client, self.assertRaises(SystemExit):
            main(['live','join','https://meet.google.com/abc-defg-hij'])
        client.assert_not_called()

    def test_start_requires_both_confirmations_before_request(self):
        for flags in ([], ['--participants-informed'], ['--allow-external-processing']):
            with self.subTest(flags=flags):
                with patch('verbalia_open.live.RecallClient') as client, self.assertRaises(SystemExit):
                    main(['live', 'start', BOT, *flags])
                client.assert_not_called()

    def test_start_and_stop_send_expected_requests(self):
        calls = []

        def opener(req, timeout):
            calls.append(req)
            return FakeResponse({})

        client = RecallClient(api_key='test-only', opener=opener)
        with patch('verbalia_open.live.RecallClient', return_value=client):
            result = main(['live', 'start', BOT, '--retention-hours', '12',
                           '--participants-informed', '--allow-external-processing'])
            self.assertEqual(result, 0)
            self.assertEqual(main(['live', 'stop', BOT]), 0)
        self.assertEqual([req.get_method() for req in calls], ['POST', 'POST'])
        self.assertTrue(calls[0].full_url.endswith(f'/{BOT}/start_recording/'))
        self.assertEqual(json.loads(calls[0].data)['retention'], {'type': 'timed', 'hours': 12})
        self.assertTrue(calls[1].full_url.endswith(f'/{BOT}/stop_recording/'))

    def test_recall_hmac_and_timestamp(self):
        key = b'example key used only in test'
        secret = 'whsec_' + base64.b64encode(key).decode()
        data = b'{"event":"transcript.data"}'
        date = '1700000000'
        sig = base64.b64encode(hmac.new(key, b'msg_1.' + date.encode() + b'.' + data, hashlib.sha256).digest()).decode()
        headers = {'webhook-id':'msg_1','webhook-timestamp':date,'webhook-signature':'v1,' + sig}
        self.assertEqual(verify_recall_signature(secret, headers, data, now=1700000000), 'msg_1')
        with self.assertRaises(ValueError):
            verify_recall_signature(secret, headers, data+b'!', now=1700000000)
        with self.assertRaises(ValueError):
            verify_recall_signature(secret, headers, data, now=1700000400)

    def test_live_event_normalization_and_draft(self):
        payload={'event':'transcript.data','data':{'bot':{'id':BOT}, 'data':{'participant':{'name':'Geometra A','id':23}, 'words':[{'text':'Propongo di approvare', 'start_timestamp':{'relative':65.2}}, {'text':'la verifica del tetto'}]}}}
        item = normalize_event(payload)
        self.assertEqual(item['second'],65.2)
        self.assertEqual(item['bot_id'],BOT)
        text = transcript_markdown([item], bot_id=BOT)
        self.assertIn('01:05',text)
        self.assertIn('DA VERIFICARE',text)
        self.assertIn('non',text.lower())
        with tempfile.TemporaryDirectory() as folder:
            log=Path(folder)/'private/events.jsonl'
            append_event(log,item)
            self.assertEqual(build_snapshot(log, BOT), text)
            self.assertEqual(main(['live','snapshot','--events',str(log),'--bot-id',BOT,'--out',str(Path(folder)/'snapshot.md')]),0)
            self.assertTrue((Path(folder)/'snapshot.md').exists())

    def test_handler_requires_bot_allowlist(self):
        with self.assertRaises(ValueError):
            make_webhook_handler('whsec_c2VjcmV0', Path('/tmp/none'), allowed_bot_ids=frozenset())

    def test_webhook_rejects_unknown_bot_and_deduplicates_signed_deliveries(self):
        key = b'webhook test key'
        secret = 'whsec_' + base64.b64encode(key).decode()
        timestamp = str(int(time()))

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'events.jsonl'
            handler = make_webhook_handler(secret, output, allowed_bot_ids=frozenset({BOT}))
            with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
                worker = Thread(target=server.serve_forever, daemon=True)
                worker.start()

                def deliver(bot_id, message_id, valid_signature=True):
                    body = json.dumps({'event': 'transcript.data', 'data': {
                        'bot': {'id': bot_id}, 'data': {'words': [{'text': 'Test'}]},
                    }}).encode()
                    signed = f'{message_id}.{timestamp}.'.encode() + body
                    signature = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
                    conn = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                    try:
                        conn.request('POST', '/recall/events', body, headers={
                            'Webhook-Id': message_id,
                            'Webhook-Timestamp': timestamp,
                            'Webhook-Signature': 'v1,' + (signature if valid_signature else 'invalid'),
                        })
                        response = conn.getresponse()
                        response.read()
                        return response.status
                    finally:
                        conn.close()

                try:
                    self.assertEqual(deliver(str(uuid4()), 'msg_unknown'), 403)
                    self.assertEqual(deliver(BOT, 'msg_invalid', False), 400)
                    self.assertFalse(output.exists())
                    with ThreadPoolExecutor(max_workers=4) as pool:
                        self.assertEqual(list(pool.map(lambda _: deliver(BOT, 'msg_valid'), range(4))), [204] * 4)
                    events = output.read_text(encoding='utf-8').splitlines()
                    self.assertEqual(len(events), 1)
                    self.assertEqual(json.loads(events[0])['bot_id'], BOT)
                finally:
                    server.shutdown()
                    worker.join(timeout=5)

if __name__ == '__main__':
    unittest.main()
