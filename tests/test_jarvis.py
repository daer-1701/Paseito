import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jarvis.agent import chat
from jarvis.store import connect, search, upsert, delete


class JarvisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "test.sqlite3")
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def record(self, **changes):
        data = {"id": "venue:cafe", "kind": "venue", "title": "Café Norte",
                "text": "Café y postres en el Paseo.", "attributes": {"floor": "2"},
                "updated_at": self.now.isoformat(), "source_url": "https://example.com/cafe"}
        return {**data, **changes}

    def test_update_is_visible_immediately(self):
        upsert(self.db, self.record())
        self.assertEqual(search(self.db, "café")[0]["title"], "Café Norte")
        upsert(self.db, self.record(title="Café Renovado", updated_at=(self.now + timedelta(seconds=1)).isoformat()))
        self.assertEqual(search(self.db, "café")[0]["title"], "Café Renovado")

    def test_expired_and_deleted_records_are_not_returned(self):
        upsert(self.db, self.record(expires_at=(self.now + timedelta(seconds=1)).isoformat()))
        self.assertEqual(search(self.db, "café", now=self.now + timedelta(seconds=2)), [])
        self.assertTrue(delete(self.db, "venue:cafe"))
        self.assertEqual(search(self.db, "café"), [])

    def test_no_evidence_does_not_invent(self):
        result = chat(self.db, "¿Dónde venden bicicletas?")
        self.assertEqual(result["sources"], [])
        self.assertIn("No tengo información confirmada", result["answer"])

    def test_private_points_are_not_searched(self):
        upsert(self.db, self.record())
        result = chat(self.db, "¿Cuántos puntos tengo?")
        self.assertEqual(result["intent"], "loyalty")
        self.assertEqual(result["sources"], [])

    def test_answer_includes_source_and_location(self):
        upsert(self.db, self.record())
        result = chat(self.db, "¿Dónde hay café?")
        self.assertEqual(result["sources"][0]["id"], "venue:cafe")
        self.assertIn("piso 2", result["answer"])

    def test_follow_up_keeps_topic(self):
        upsert(self.db, self.record())
        first = chat(self.db, "Busco café")
        second = chat(self.db, "¿Dónde queda?", first["session_id"])
        self.assertEqual(second["sources"][0]["id"], "venue:cafe")


if __name__ == "__main__":
    unittest.main()
