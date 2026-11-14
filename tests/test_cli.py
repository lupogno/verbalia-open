import json
import tempfile
import unittest
from pathlib import Path
from verbalia_open.cli import main, create_bundle
from verbalia_open.render import render_minutes, actions_csv

ROOT = Path(__file__).resolve().parents[1]


class TestCli(unittest.TestCase):
    def test_bundle_creates_four_files(self):
        data = json.loads((ROOT / "examples/condominio.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            result = create_bundle(data, Path(tmp))
            self.assertEqual(len(result), 4)
            self.assertTrue(all(p.exists() and p.stat().st_size > 10 for p in result.values()))
            self.assertEqual(json.loads((Path(tmp) / "audit.json").read_text(encoding="utf-8"))["approval_state"], "NOT_APPROVED")

    def test_md_render(self):
        data = json.loads((ROOT / "examples/cda.json").read_text(encoding="utf-8"))
        output = render_minutes(data)
        self.assertIn("BOZZA DA VERIFICARE", output)
        self.assertIn("Presidente", output)
        self.assertIn("APP-01", output)

    def test_csv(self):
        data = json.loads((ROOT / "examples/condominio.json").read_text(encoding="utf-8"))
        self.assertIn("owner", actions_csv(data))

    def test_external_processing_is_opt_in(self):
        with self.assertRaises(SystemExit):
            main(["ai-draft", "examples/appunti_condominio.txt", "--type", "condominio", "--model", "mock", "--out", "x.json"])

    def test_error_exit_nonzero(self):
        self.assertEqual(main(["validate", str(ROOT / "examples/caso_critico.json")]), 1)
