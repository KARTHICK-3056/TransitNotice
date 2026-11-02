import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("transitnotice.alert_service")
IST = ZoneInfo("Asia/Kolkata")

def dispatch_alerts_for_notice(conn, notice_id: str, revision_id: int):
    """
    Evaluates all subscribers against the notice and logs deduplicated alerts.
    Enforces UNIQUE(notice_id, revision_id, subscriber_id).
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM notices WHERE notice_id = ?", (notice_id,))
    notice = cur.fetchone()
    if not notice:
        return

    # Fetch routes and stations for this notice
    cur.execute("SELECT route_id FROM notice_routes WHERE notice_id = ?", (notice_id,))
    routes = [r[0].lower() for r in cur.fetchall()]

    cur.execute("SELECT station FROM notice_stations WHERE notice_id = ?", (notice_id,))
    stations = [s[0].lower() for s in cur.fetchall()]

    area_low = notice["area"].lower()
    type_low = notice["type"].lower()

    # Fetch all subscribers
    cur.execute("SELECT subscriber_id, email, subscriber_filter FROM subscribers")
    subscribers = cur.fetchall()

    now_iso = datetime.now(IST).isoformat()

    for sub in subscribers:
        sub_id = sub["subscriber_id"]
        try:
            filters = json.loads(sub["subscriber_filter"])
        except Exception:
            filters = {}

        matched = False
        target_routes = [r.lower() for r in filters.get("routes", [])]
        target_stations = [s.lower() for s in filters.get("stations", [])]
        target_areas = [a.lower() for a in filters.get("areas", [])]
        target_types = [t.lower() for t in filters.get("types", [])]

        if not target_routes and not target_stations and not target_areas and not target_types:
            # Subscribed to all
            matched = True
        else:
            if target_routes and any(r in routes for r in target_routes):
                matched = True
            elif target_stations and any(s in stations for s in target_stations):
                matched = True
            elif target_areas and any(a in area_low for a in target_areas):
                matched = True
            elif target_types and any(t in type_low for t in target_types):
                matched = True

        if matched:
            cur.execute(
                """
                INSERT OR IGNORE INTO alert_log (notice_id, revision_id, subscriber_id, alert_status, alerted_at)
                VALUES (?, ?, ?, 'sent', ?)
                """,
                (notice_id, revision_id, sub_id, now_iso)
            )

def subscribe_user(conn, email: str, filters_dict: dict) -> int:
    """Creates or updates a subscriber with their preference filter JSON."""
    now_iso = datetime.now(IST).isoformat()
    filter_json = json.dumps(filters_dict)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO subscribers (email, subscriber_filter, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            subscriber_filter = excluded.subscriber_filter
        """,
        (email.strip().lower(), filter_json, now_iso)
    )
    cur.execute("SELECT subscriber_id FROM subscribers WHERE email = ?", (email.strip().lower(),))
    row = cur.fetchone()
    return row[0] if row else 0

