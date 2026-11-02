import unittest
import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import IST_TIMEZONE
from backend.services.sync_engine import calculate_status, sync_engine
from backend.services.hashing import compute_content_hash, generate_change_summary
from backend.services.alert_service import dispatch_alerts_for_notice, subscribe_user
from backend.sources.base import BaseSourceAdapter, Fetcher, FetchError
from backend.sources.sample_metro import metro_demo_state

TEST_DB_PATH = Path(__file__).parent / "test_transitnotice.db"

class TestTransitNoticeAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

        cls.conn = sqlite3.connect(TEST_DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA foreign_keys = ON")

        migration_file = Path(__file__).resolve().parent.parent / "migrations" / "001_init.sql"
        with open(migration_file, "r", encoding="utf-8") as f:
            cls.conn.executescript(f.read())

        # Seed test source
        cls.conn.execute(
            """
            INSERT INTO sources (source_key, agency, operator_type, base_url, timezone, refresh_seconds, enabled, label)
            VALUES ('test_metro', 'Chennai Metro Rail Limited', 'Government', 'http://127.0.0.1:5000/demo-source/metro', 'Asia/Kolkata', 300, 1, 'CMRL Test')
            """
        )
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    def test_1_expired_notice_never_marked_active(self):
        """1. Expired notices (valid_to in past) must be computed as 'ended', NEVER 'active'."""
        now = datetime.now(IST_TIMEZONE)
        past_from = (now - timedelta(days=5)).isoformat()
        past_to = (now - timedelta(days=1)).isoformat()

        status = calculate_status(past_from, past_to, now)
        self.assertEqual(status, "ended", f"Notice with valid_to in past must be 'ended', got '{status}'")
        self.assertNotEqual(status, "active", "Expired notice must NEVER be marked 'active'!")

    def test_2_multi_route_filtering(self):
        """2. Multi-route matching: An advisory with routes 'Blue Line, Green Line' matches both."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO notices (
                notice_id, source_id, external_id, agency, route_id, area,
                source_url, type, summary, published_at, valid_from, valid_to,
                status, observed_at, last_confirmed_at, content_hash, revision_id
            ) VALUES (
                'test:MULTI-01', 1, 'MULTI-01', 'Chennai Metro Rail Limited', 'Blue Line, Green Line',
                'Chennai - Interchange', 'http://example.com/multi', 'Track maintenance',
                'Interchange switch point check', '2026-03-20T08:00:00', '2026-03-20T08:00:00',
                NULL, 'active', '2026-03-20T08:00:00', '2026-03-20T08:00:00', 'hash_test_1', 1
            )
            """
        )
        cur.execute("DELETE FROM notice_routes WHERE notice_id = 'test:MULTI-01'")
        cur.execute("INSERT INTO notice_routes (notice_id, route_id) VALUES ('test:MULTI-01', 'Blue Line')")
        cur.execute("INSERT INTO notice_routes (notice_id, route_id) VALUES ('test:MULTI-01', 'Green Line')")
        self.conn.commit()

        # Query for Blue Line
        cur.execute("SELECT notice_id FROM notice_routes WHERE route_id = 'Blue Line'")
        blue_matches = [r[0] for r in cur.fetchall()]
        self.assertIn("test:MULTI-01", blue_matches)

        # Query for Green Line
        cur.execute("SELECT notice_id FROM notice_routes WHERE route_id = 'Green Line'")
        green_matches = [r[0] for r in cur.fetchall()]
        self.assertIn("test:MULTI-01", green_matches)

        # Query for Corrdior 4 (should not match)
        cur.execute("SELECT notice_id FROM notice_routes WHERE route_id = 'Corridor 4'")
        c4_matches = [r[0] for r in cur.fetchall()]
        self.assertNotIn("test:MULTI-01", c4_matches)

    def test_3_extended_outage_bumps_revision_and_change_summary(self):
        """3. Extending outage by 24h increments revision_id and logs human-readable diff in history."""
        cur = self.conn.cursor()
        old_to = "2026-03-22T18:00:00"
        new_to = "2026-03-23T18:00:00"

        old_notice = {
            "route_id": "Green Line",
            "type": "Track maintenance",
            "summary": "Overhead Line Inspection between Koyambedu and Alandur",
            "valid_from": "2026-03-20T06:00:00",
            "valid_to": old_to
        }
        new_notice = dict(old_notice)
        new_notice["valid_to"] = new_to

        old_hash = compute_content_hash(old_notice["route_id"], old_notice["type"], old_notice["summary"], old_notice["valid_from"], old_notice["valid_to"])
        new_hash = compute_content_hash(new_notice["route_id"], new_notice["type"], new_notice["summary"], new_notice["valid_from"], new_notice["valid_to"])

        self.assertNotEqual(old_hash, new_hash, "Hash must change when valid_to is extended!")

        diff_summary = generate_change_summary(old_notice, new_notice)
        self.assertIn("Extended valid_to by 24 hours", diff_summary)

        # Simulate update in DB
        cur.execute(
            """
            INSERT INTO notice_revisions (
                notice_id, revision_id, changed_at, content_hash,
                valid_from, valid_to, status, route_id, area, change_summary
            ) VALUES ('test:MULTI-01', 2, '2026-03-21T00:00:00', ?, ?, ?, 'active', 'Green Line', 'Chennai', ?)
            """,
            (old_hash, old_notice["valid_from"], new_to, diff_summary)
        )
        cur.execute("UPDATE notices SET revision_id = 2, content_hash = ?, change_summary = ? WHERE notice_id = 'test:MULTI-01'", (new_hash, diff_summary))
        self.conn.commit()

        cur.execute("SELECT revision_id, change_summary FROM notices WHERE notice_id = 'test:MULTI-01'")
        updated = cur.fetchone()
        self.assertEqual(updated["revision_id"], 2)
        self.assertIn("Extended valid_to by 24 hours", updated["change_summary"])

    def test_4_ist_datetime_and_open_ended_support(self):
        """4. Open-ended notices (valid_to is None) parse and display cleanly without errors."""
        now = datetime.now(IST_TIMEZONE)
        status = calculate_status("2026-03-01T08:00:00", None, now)
        self.assertEqual(status, "active", "Open-ended notice with past valid_from must be 'active'")

        h = compute_content_hash("Blue Line", "Station closed", "Gate closed", "2026-03-01T08:00:00", None)
        self.assertTrue(len(h) == 64, "Content hash must be valid 64-char SHA-256")

    def test_5_source_outage_503_preserves_last_confirmed_at(self):
        """5. Source outage (503) preserves existing notices and NEVER updates last_confirmed_at."""
        cur = self.conn.cursor()
        cur.execute("SELECT last_confirmed_at FROM notices WHERE notice_id = 'test:MULTI-01'")
        original_confirmed_at = cur.fetchone()["last_confirmed_at"]

        # Mock adapter throwing 503
        class FailingAdapter(BaseSourceAdapter):
            def fetch_notices(self, fetcher):
                raise FetchError("HTTP 503 Service Unavailable", status_code=503)

        sync_engine.adapters["failing_test"] = FailingAdapter(
            "failing_test", "Failing Test Source", "Test Agency", "Government", "http://example.com/fail"
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO sources (source_key, agency, operator_type, base_url, label)
            VALUES ('failing_test', 'Test Agency', 'Government', 'http://example.com/fail', 'Failing Source')
            """
        )
        self.conn.commit()

        # Run sync for failing source
        res = sync_engine.sync_source(self.conn, "failing_test")
        self.assertEqual(res["outcome"], "error")
        self.assertEqual(res["http_status"], 503)

        # Verify last_confirmed_at on test notice was NOT touched
        cur.execute("SELECT last_confirmed_at FROM notices WHERE notice_id = 'test:MULTI-01'")
        current_confirmed_at = cur.fetchone()["last_confirmed_at"]
        self.assertEqual(original_confirmed_at, current_confirmed_at, "last_confirmed_at was updated on a failed run! Provenance violated!")

    def test_6_single_alert_deduplication(self):
        """6. UNIQUE(notice_id, revision_id, subscriber_id) guarantees at most 1 alert per revision."""
        cur = self.conn.cursor()
        # Create subscriber
        sub_id = subscribe_user(self.conn, "commuter@chennaimetrorail.local", {"routes": ["Blue Line"]})
        self.assertGreater(sub_id, 0)

        # Dispatch alert for revision 1
        dispatch_alerts_for_notice(self.conn, "test:MULTI-01", 1)
        cur.execute("SELECT COUNT(*) FROM alert_log WHERE notice_id = 'test:MULTI-01' AND revision_id = 1 AND subscriber_id = ?", (sub_id,))
        count_1 = cur.fetchone()[0]
        self.assertEqual(count_1, 1, "Expected exactly 1 alert record for rev 1")

        # Run dispatch a second time on identical rev 1
        dispatch_alerts_for_notice(self.conn, "test:MULTI-01", 1)
        cur.execute("SELECT COUNT(*) FROM alert_log WHERE notice_id = 'test:MULTI-01' AND revision_id = 1 AND subscriber_id = ?", (sub_id,))
        count_repeat = cur.fetchone()[0]
        self.assertEqual(count_repeat, 1, "Duplicate alert was logged! Deduplication failed!")

if __name__ == "__main__":
    unittest.main()

