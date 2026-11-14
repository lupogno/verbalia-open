import unittest
from verbalia_open.privacy import mask_contacts
from verbalia_open.ai import _extract_json


class TestPrivacyAndAI(unittest.TestCase):
    def test_mask_email(self):
        self.assertIn("[EMAIL]", mask_contacts("contatta abc@example.it"))

    def test_extract_json(self):
        self.assertEqual(_extract_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_reject_array(self):
        with self.assertRaises(ValueError):
            _extract_json("[]")
