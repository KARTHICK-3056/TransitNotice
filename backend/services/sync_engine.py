import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional

from backend.config import IST_TIMEZONE
from backend.sources.base import Fetcher, FetchError
from backend.sources.cmrl_diversions import CMRLDiversionsAdapter
from backend.sources.cmrl_press import CMRLPressAdapter
from backend.sources.sample_metro import SampleMetroAdapter
from backend.sources.demo_private_bus import DemoPrivateBusAdapter
from backend.services.hashing import compute_content_hash, generate_change_summary
from backend.services.alert_service import dispatch_alerts_for_notice

logger = logging.getLogger("transitnotice.sync_engine")

def calculate_status(valid_from_str: str, valid_to_str: Optional[str], now: datetime) -> str:
    """
    Computes effective status according to business logic:
    - If valid_to in past -> 'ended' (never active)
    - If valid_from > now -> 'upcoming'
    - If valid_from <= now and (valid_to is NULL or valid_to >= now) -> 'active'
    """
    def parse_dt(s):
        if not s:
            return None
        cleaned = s.replace("Z", "").strip()
        try:
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST_TIMEZONE)
            return dt
        except Exception:
            return None

    dt_from = parse_dt(valid_from_str) or now
    dt_to = parse_dt(valid_to_str)

    if dt_to is not None and dt_to < now:
        return "ended"
    if dt_from > now:
        return "upcoming"
    return "active"

class SyncEngine:
    def __init__(self):
        self.fetcher = Fetcher()
        self.adapters = {
            "cmrl": CMRLDiversionsAdapter(),
            "cmrl_press": CMRLPressAdapter(),
            "sample_metro": SampleMetroAdapter(),
            "demo_private_bus": DemoPrivateBusAdapter()
        }

    def sync_source(self, conn, source_key: str) -> Dict[str, Any]:
        adapter = self.adapters.get(source_key)
        if not adapter:
            return {"error": f"Unknown source {source_key}"}

        cur = conn.cursor()
        cur.execute("SELECT source_id, refresh_seconds FROM sources WHERE source_key = ?", (source_key,))
        source_row = cur.fetchone()
        if not source_row:
            return {"error": f"Source {source_key} not found in database"}

        source_id = source_row["source_id"]
        refresh_seconds = source_row["refresh_seconds"] or 300

        now = datetime.now(IST_TIMEZONE)
        started_at = now.isoformat()
        outcome = "ok"
        http_status = 200
        error_msg = None

        new_count = 0
        revised_count = 0
        withdrawn_count = 0
        items_parsed = 0
        items_skipped = 0

        parsed_items: List[Dict[str, Any]] = []

        try:
            parsed_items = adapter.fetch_notices(self.fetcher)
            items_parsed = len(parsed_items)
        except FetchError as fe:
            outcome = "blocked" if fe.status_code == 403 else "error"
            http_status = fe.status_code or 500
            error_msg = str(fe)
            logger.error(f"[{source_key}] Fetch failed: {fe}")
        except Exception as ex:
            outcome = "error"
            http_status = 500
            error_msg = f"Unexpected parse error: {str(ex)}"
            logger.error(f"[{source_key}] Error: {ex}", exc_info=True)

        finished_at = datetime.now(IST_TIMEZONE).isoformat()

        if outcome == "ok":
            seen_external_ids = set()

            for item in parsed_items:
                ext_id = item["external_id"]
                seen_external_ids.add(ext_id)
                notice_id = f"{source_key}:{ext_id}"

                route_id = item["route_id"]
                area = item["area"]
                source_url = item["source_url"]
                adv_type = item["type"]
                summary = item["summary"]
                published_at = item["published_at"]
                valid_from = item["valid_from"]
                valid_to = item.get("valid_to")
                # Ensure valid_to >= valid_from
                if valid_to and valid_from and valid_to < valid_from:
                    valid_to = valid_from

                status = calculate_status(valid_from, valid_to, now)

                content_hash = compute_content_hash(route_id, adv_type, summary, valid_from, valid_to)

                # Check if notice already exists
                cur.execute("SELECT * FROM notices WHERE notice_id = ?", (notice_id,))
                existing = cur.fetchone()

                if not existing:
                    # Brand new notice (Revision 1)
                    cur.execute(
                        """
                        INSERT INTO notices (
                            notice_id, source_id, external_id, agency, route_id, area,
                            source_url, type, summary, published_at, valid_from, valid_to,
                            status, observed_at, last_confirmed_at, content_hash,
                            revision_id, change_summary, alert_status, alerted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'Initial observation', 'sent', ?)
                        """,
                        (
                            notice_id, source_id, ext_id, item["agency"], route_id, area,
                            source_url, adv_type, summary, published_at, valid_from, valid_to,
                            status, started_at, started_at, content_hash, started_at
                        )
                    )
                    new_count += 1

                    # Insert routes and stations
                    for r in item.get("routes", [route_id]):
                        cur.execute("INSERT OR IGNORE INTO notice_routes (notice_id, route_id) VALUES (?, ?)", (notice_id, r.strip()))
                    for s in item.get("stations", []):
                        cur.execute("INSERT OR IGNORE INTO notice_stations (notice_id, station) VALUES (?, ?)", (notice_id, s.strip()))

                    dispatch_alerts_for_notice(conn, notice_id, 1)

                else:
                    # Existing notice: compare content_hash
                    if existing["content_hash"] == content_hash:
                        # Unchanged content: ONLY update last_confirmed_at and dynamic status
                        cur.execute(
                            """
                            UPDATE notices SET
                                last_confirmed_at = ?,
                                status = ?
                            WHERE notice_id = ?
                            """,
                            (started_at, status, notice_id)
                        )
                    else:
                        # Content changed! Increment revision_id, append to notice_revisions, update notice
                        old_rev_id = existing["revision_id"]
                        cur.execute("SELECT COALESCE(MAX(revision_id), 0) FROM notice_revisions WHERE notice_id = ?", (notice_id,))
                        max_rev_row = cur.fetchone()
                        max_rev = max_rev_row[0] if max_rev_row else 0
                        new_rev_id = max(old_rev_id + 1, max_rev + 1)
                        chg_summary = generate_change_summary(dict(existing), item)

                        # Insert revision snapshot
                        cur.execute(
                            """
                            INSERT OR REPLACE INTO notice_revisions (
                                notice_id, revision_id, changed_at, content_hash,
                                valid_from, valid_to, status, route_id, area, change_summary
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                notice_id, new_rev_id, started_at, existing["content_hash"],
                                existing["valid_from"], existing["valid_to"], existing["status"],
                                existing["route_id"], existing["area"], chg_summary
                            )
                        )

                        cur.execute(
                            """
                            UPDATE notices SET
                                route_id = ?,
                                area = ?,
                                type = ?,
                                summary = ?,
                                valid_from = ?,
                                valid_to = ?,
                                status = ?,
                                last_confirmed_at = ?,
                                content_hash = ?,
                                revision_id = ?,
                                change_summary = ?
                            WHERE notice_id = ?
                            """,
                            (
                                route_id, area, adv_type, summary, valid_from, valid_to,
                                status, started_at, content_hash, new_rev_id, chg_summary, notice_id
                            )
                        )
                        revised_count += 1

                        # Update routes & stations
                        cur.execute("DELETE FROM notice_routes WHERE notice_id = ?", (notice_id,))
                        for r in item.get("routes", [route_id]):
                            cur.execute("INSERT OR IGNORE INTO notice_routes (notice_id, route_id) VALUES (?, ?)", (notice_id, r.strip()))

                        cur.execute("DELETE FROM notice_stations WHERE notice_id = ?", (notice_id,))
                        for s in item.get("stations", []):
                            cur.execute("INSERT OR IGNORE INTO notice_stations (notice_id, station) VALUES (?, ?)", (notice_id, s.strip()))

                        dispatch_alerts_for_notice(conn, notice_id, new_rev_id)

            # Check for WITHDRAWN notices (disappeared from healthy feed before valid_to)
            cur.execute("SELECT * FROM notices WHERE source_id = ? AND status = 'active'", (source_id,))
            active_existing = cur.fetchall()
            for adv in active_existing:
                if adv["external_id"] not in seen_external_ids:
                    # Disappeared before expiry
                    cur.execute(
                        """
                        UPDATE notices SET
                            status = 'withdrawn',
                            change_summary = 'Withdrawn from official agency feed prior to scheduled expiry'
                        WHERE notice_id = ?
                        """,
                        (adv["notice_id"],)
                    )
                    withdrawn_count += 1

            # Update sources table on success
            next_run = (now + timedelta(seconds=refresh_seconds)).isoformat()
            cur.execute(
                """
                UPDATE sources SET
                    last_attempt_at = ?,
                    last_success_at = ?,
                    consecutive_failures = 0,
                    next_run_at = ?,
                    last_error = NULL
                WHERE source_id = ?
                """,
                (started_at, started_at, next_run, source_id)
            )

        else:
            # Source failed: NEVER update last_confirmed_at on existing notices!
            cur.execute(
                """
                UPDATE sources SET
                    last_attempt_at = ?,
                    consecutive_failures = consecutive_failures + 1,
                    last_error = ?
                WHERE source_id = ?
                """,
                (started_at, error_msg, source_id)
            )

        # Record fetch_run
        cur.execute(
            """
            INSERT INTO fetch_runs (
                source_id, started_at, finished_at, outcome, http_status,
                items_parsed, items_skipped, new_count, revised_count,
                withdrawn_count, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id, started_at, finished_at, outcome, http_status,
                items_parsed, items_skipped, new_count, revised_count,
                withdrawn_count, error_msg
            )
        )

        return {
            "source_key": source_key,
            "outcome": outcome,
            "http_status": http_status,
            "items_parsed": items_parsed,
            "new_count": new_count,
            "revised_count": revised_count,
            "withdrawn_count": withdrawn_count,
            "error": error_msg
        }

    def sync_all(self, conn) -> List[Dict[str, Any]]:
        results = []
        cur = conn.cursor()
        cur.execute("SELECT source_key FROM sources WHERE enabled = 1")
        rows = cur.fetchall()
        for r in rows:
            res = self.sync_source(conn, r["source_key"])
            results.append(res)
        return results

sync_engine = SyncEngine()

