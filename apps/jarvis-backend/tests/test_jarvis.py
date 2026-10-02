import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from jarvis.agent import chat, llm_answer
from jarvis.stimulus import gaze
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

    def test_openai_responses_contract(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def read(self, *_):
                return json.dumps({"output": [{"type": "message", "content": [
                    {"type": "output_text", "text": "El café está en el piso 2."}]}]}).encode()

        captured = []

        def fake_urlopen(request, timeout):
            captured.append((request, timeout))
            return Response()

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}), \
                patch("urllib.request.urlopen", fake_urlopen):
            answer = llm_answer("¿Dónde está?", [{**self.record(), "attributes": {"floor": "2"}}], [])

        self.assertEqual(answer, "El café está en el piso 2.")
        request, timeout = captured[0]
        self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(json.loads(request.data)["store"], False)
        self.assertEqual(timeout, 12)

    def test_gaze_activates_once_after_sustained_dwell(self):
        upsert(self.db, self.record())
        upsert(self.db, self.record(id="venue:other-cafe", title="Café Sur"))
        self.assertEqual(gaze(self.db, "gaze-demo", "venue:cafe", 500)["reason"], "dwell_too_short")
        activated = gaze(self.db, "gaze-demo", "venue:cafe", 1000)
        self.assertTrue(activated["triggered"])
        self.assertEqual(activated["chat"]["sources"][0]["id"], "venue:cafe")
        self.assertEqual(len(activated["chat"]["sources"]), 1)
        self.assertEqual(gaze(self.db, "gaze-demo", "venue:cafe", 1000)["reason"], "cooldown")


if __name__ == "__main__":
    unittest.main()
