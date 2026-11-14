import copy
import json
import unittest
from pathlib import Path
from verbalia_open.engine import assess

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class TestEngine(unittest.TestCase):
    def test_condominium_second_call_arithmetic(self):
        report = assess(load("condominio.json"))
        self.assertEqual(report["resolutions"][0]["constituted"], True)
        self.assertEqual(report["resolutions"][0]["favorable"], True)
        self.assertFalse(any(x["level"] == "error" for x in report["issues"]))

    def test_cda_2388_numeric_threshold(self):
        report = assess(load("cda.json"))
        self.assertTrue(report["resolutions"][0]["constituted"])
        self.assertTrue(report["resolutions"][0]["favorable"])

    def test_missing_evidence(self):
        data = load("condominio.json")
        data["agenda"][0]["evidence"] = ["NON-ESISTE"]
        codes = {x["code"] for x in assess(data)["issues"]}
        self.assertIn("EVIDENCE_MISSING", codes)

    def test_duplicate_vote_detected(self):
        data = load("condominio.json")
        data["agenda"][0]["votes"].append({"voter_id": "U1", "choice": "favorevole"})
        codes = {x["code"] for x in assess(data)["issues"]}
        self.assertIn("VOTE_DUPLICATE", codes)

    def test_under_threshold_first_call(self):
        data = load("condominio.json")
        data["convocation"] = 1
        report = assess(data)
        self.assertFalse(report["resolutions"][0]["constituted"])
        self.assertIn("CONSTITUTION_THRESHOLD", [x["code"] for x in report["issues"]])

    def test_qualified_supermajority_fails(self):
        data = load("condominio.json")
        data["agenda"][0]["quorum_rule"] = "due_terzi_valore"
        report = assess(data)
        self.assertFalse(report["resolutions"][0]["favorable"])
        self.assertIn("APPROVAL_THRESHOLD", [x["code"] for x in report["issues"]])

    def test_manual_rule_is_indeterminate(self):
        data = load("condominio.json")
        data["agenda"][0]["quorum_rule"] = "manuale"
        report = assess(data)
        self.assertIsNone(report["resolutions"][0]["favorable"])

    def test_audit_privacy_and_missing_vote(self):
        report = assess(load("caso_critico.json"))
        codes = {x["code"] for x in report["issues"]}
        self.assertIn("PRIVACY_REVIEW", codes)
        self.assertIn("VOTES_INCOMPLETE", codes)
        self.assertIn("NOTICES", codes)
        self.assertIn("DECISION_UNSOURCED", codes)

    def test_not_present_vote(self):
        data = load("condominio.json")
        data["agenda"][0]["votes"][0]["voter_id"] = "U4"
        self.assertIn("VOTE_NONPRESENT", [x["code"] for x in assess(data)["issues"]])

    def test_board_proxy_forbidden(self):
        data = load("cda.json")
        data["attendees"][1]["represented_by"] = "A1"
        self.assertIn("BOARD_PROXY", [x["code"] for x in assess(data)["issues"]])

    def test_bad_date(self):
        data = load("cda.json")
        data["date"] = "domani"
        self.assertIn("BAD_DATE", [x["code"] for x in assess(data)["issues"]])

    def test_no_fake_approval(self):
        data = load("condominio.json")
        data["agenda"][0]["votes"] = []
        self.assertIsNone(assess(data)["resolutions"][0]["favorable"])

    def test_non_legal_work_meeting(self):
        data = load("cantiere.json")
        report = assess(data)
        self.assertIsNone(report["resolutions"][0]["favorable"])

    def test_invalid_total_does_not_crash(self):
        data = load("condominio.json")
        data["total_millesimi"] = "non noto"
        report = assess(data)
        self.assertIn("TOTAL_MILLESIMI", [x["code"] for x in report["issues"]])

    def test_duplicate_vote_suspends_numeric_result(self):
        data = load("condominio.json")
        data["agenda"][0]["votes"].append({"voter_id": "U1", "choice": "contrario"})
        self.assertIsNone(assess(data)["resolutions"][0]["favorable"])

    def test_board_without_confirmed_statute_is_indeterminate(self):
        data = load("cda.json")
        data["statute_reviewed"] = False
        self.assertIsNone(assess(data)["resolutions"][0]["favorable"])

    def test_used_recording_without_authorization_is_flagged(self):
        data = load("cda.json")
        data["used_recording"] = True
        data["recording_authorization"] = "not_applicable"
        self.assertIn("PRIVACY_REVIEW", [x["code"] for x in assess(data)["issues"]])

    def test_root_invalid(self):
        self.assertEqual(assess([])["status"], "da_verificare")
