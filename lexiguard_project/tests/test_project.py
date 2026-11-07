import os
import tempfile
import unittest
from unittest.mock import patch
from backend.engine import analyze, apply_suggestions
from backend import secure_store

class GrammarTests(unittest.TestCase):
    def test_common_errors(self):
        result = analyze('i dont recieve teh message')
        self.assertIn("don't", result['corrected'])
        self.assertIn('receive', result['corrected'])
        self.assertIn('the message', result['corrected'])
    def test_offsets(self):
        text = 'This  is  fine.'
        result = analyze(text)
        for s in result['suggestions']:
            self.assertEqual(text[s['start']:s['end']], s['original'])
        self.assertEqual(apply_suggestions(text, result['suggestions']), result['corrected'])
    def test_empty(self):
        self.assertEqual(analyze('')['metrics']['words'], 0)

class VaultTests(unittest.TestCase):
    def test_roundtrip_and_wrong_password(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(secure_store, 'DB_PATH', __import__('pathlib').Path(directory) / 'vault.db'):
                data = secure_store.save('Secret title', 'A secret draft 👋', 'correct horse battery staple')
                self.assertEqual(secure_store.load(data['id'], 'correct horse battery staple')['content'], 'A secret draft 👋')
                with self.assertRaises(ValueError):
                    secure_store.load(data['id'], 'wrong passphrase')
                db_bytes = secure_store.DB_PATH.read_bytes()
                self.assertNotIn(b'Secret title', db_bytes)
                self.assertNotIn(b'A secret draft', db_bytes)
                self.assertTrue(secure_store.remove(data['id']))
                self.assertIsNone(secure_store.load(data['id'], 'correct horse battery staple'))

if __name__ == '__main__':
    unittest.main()
