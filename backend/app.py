import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, Dict, Any, List
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from backend.config import IST_TIMEZONE, ADMIN_TOKEN, HOST, PORT, BASE_DIR
from backend.db import get_db, init_db
from backend.sources.sample_metro import metro_demo_state
from backend.sources.demo_private_bus import PRIVATE_BUS_RSS_XML
from backend.services.sync_engine import sync_engine
from backend.services.alert_service import subscribe_user

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("transitnotice")

app = Flask(__name__)
CORS(app)

FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

# Helper function to format relative time
def format_relative_time(dt_str: str) -> str:
    if not dt_str:
        return "never checked"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST_TIMEZONE)
        now = datetime.now(IST_TIMEZONE)
        diff_sec = int((now - dt).total_seconds())
        if diff_sec < 10:
            return "checked just now"
        if diff_sec < 60:
            return f"checked {diff_sec}s ago"
        diff_min = diff_sec // 60
        if diff_min < 60:
            return f"checked {diff_min}m ago"
        diff_hours = diff_min // 60
        if diff_hours < 24:
            return f"checked {diff_hours}h ago"
        return f"checked {diff_hours // 24}d ago"
    except Exception:
        return dt_str

def format_ist_datetime(dt_str: Optional[str]) -> Optional[str]:
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST_TIMEZONE)
        return dt.strftime("%d %b %Y %H:%M IST")
    except Exception:
        return dt_str

# ==============================================================================
# DEMO SOURCES ENDPOINTS (For Mentor Live Testing)
# ==============================================================================

@app.route("/demo-source/metro", methods=["GET"])
def get_demo_metro_html():
    if metro_demo_state.simulate_503:
        return Response("HTTP 503 Service Unavailable: Simulated Upstream Failure", status=503, mimetype="text/plain")

    cards = []
    for n in metro_demo_state.notices:
        stations_html = "".join([f'<span class="station">{s}</span>' for s in n.get("stations", [])])
        cards.append(f"""
        <div class="advisory-card" data-id="{n['id']}">
            <h3 class="title">{n['title']}</h3>
            <span class="route">{n['route']}</span>
            <div class="stations">{stations_html}</div>
            <span class="area">{n['area']}</span>
            <span class="type">{n['type']}</span>
            <p class="summary">{n['summary']}</p>
            <time class="valid-from">{n['valid_from']}</time>
            <time class="valid-to">{n['valid_to'] if n['valid_to'] else 'None'}</time>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html>
<head><title>Sample Chennai Transit Portal</title></head>
<body>
    <h1>Sample Chennai Transit (demo agency) - Service Bulletins</h1>
    <div class="bulletins">
        {"".join(cards)}
    </div>
</body>
</html>"""
    return Response(html, status=200, mimetype="text/html")

@app.route("/demo-source/private_coaches.xml", methods=["GET"])
def get_demo_private_coaches_xml():
    return Response(PRIVATE_BUS_RSS_XML, status=200, mimetype="application/xml")

@app.route("/demo-source/metro/extend-24h", methods=["POST"])
def demo_extend_24h():
    data = request.get_json(silent=True) or {}
    notice_id = data.get("notice_id", "METRO-DEMO-01")
    res = metro_demo_state.extend_24h(notice_id)
    with get_db() as conn:
        sync_engine.sync_source(conn, "sample_metro")
    return jsonify(res)

@app.route("/demo-source/metro/inject-open-ended", methods=["POST"])
def demo_inject_open_ended():
    res = metro_demo_state.inject_open_ended()
    with get_db() as conn:
        sync_engine.sync_source(conn, "sample_metro")
    return jsonify(res)

@app.route("/demo-source/metro/simulate-503", methods=["POST"])
def demo_simulate_503():
    res = metro_demo_state.set_503(True)
    with get_db() as conn:
        sync_engine.sync_source(conn, "sample_metro")
    return jsonify(res)

@app.route("/demo-source/metro/recover", methods=["POST"])
def demo_recover():
    res = metro_demo_state.set_503(False)
    with get_db() as conn:
        sync_engine.sync_source(conn, "sample_metro")
    return jsonify(res)

@app.route("/demo-source/metro/reset", methods=["POST"])
def demo_reset():
    metro_demo_state.reset()
    with get_db() as conn:
        sync_engine.sync_source(conn, "sample_metro")
    return jsonify({"ok": True, "message": "Demo metro feed reset to original baseline"})

# ==============================================================================
# CORE REST API
# ==============================================================================

@app.route("/api/notices", methods=["GET"])
def get_notices():
    op_type = request.args.get("operator_type")
    agency = request.args.get("agency")
    route = request.args.get("route")
    station = request.args.get("station")
    area = request.args.get("area")
    adv_type = request.args.get("type")
    show = request.args.get("show", "all")  # all, in_effect_now, upcoming, ended, withdrawn
    travel_day = request.args.get("travel_day")
    year = request.args.get("year")
    end_date_filter = request.args.get("end_date")  # has_end_date, open_ended
    sort_by = request.args.get("sort", "newest")  # newest, oldest, expiring_soon
    q = request.args.get("q")

    with get_db() as conn:
        cur = conn.cursor()

        # Build query
        query = """
            SELECT n.*, s.operator_type, s.label as source_label
            FROM notices n
            JOIN sources s ON n.source_id = s.source_id
            WHERE 1=1
        """
        params = []

        if op_type and op_type != "all":
            query += " AND s.operator_type = ?"
            params.append(op_type)

        if agency and agency != "all":
            query += " AND n.agency = ?"
            params.append(agency)

        if area and area != "all":
            query += " AND n.area = ?"
            params.append(area)

        if adv_type and adv_type != "all":
            query += " AND n.type = ?"
            params.append(adv_type)

        if show == "in_effect_now":
            query += " AND n.status = 'active'"
        elif show == "upcoming":
            query += " AND n.status = 'upcoming'"
        elif show == "ended":
            query += " AND n.status IN ('ended', 'cancelled')"
        elif show == "withdrawn":
            query += " AND n.status = 'withdrawn'"
        elif show == "active_and_upcoming":
            query += " AND n.status IN ('active', 'upcoming')"

        if route and route != "all":
            query += " AND n.notice_id IN (SELECT notice_id FROM notice_routes WHERE route_id = ?)"
            params.append(route)

        if station and station != "all":
            query += " AND n.notice_id IN (SELECT notice_id FROM notice_stations WHERE station = ?)"
            params.append(station)

        if year and year != "all":
            query += " AND n.published_at LIKE ?"
            params.append(f"{year}%")

        if end_date_filter == "open_ended":
            query += " AND n.valid_to IS NULL"
        elif end_date_filter == "has_end_date":
            query += " AND n.valid_to IS NOT NULL"

        if q:
            search_pattern = f"%{q.strip()}%"
            query += """ AND (
                n.summary LIKE ? OR
                n.area LIKE ? OR
                n.agency LIKE ? OR
                n.route_id LIKE ? OR
                n.notice_id LIKE ?
            )"""
            params.extend([search_pattern] * 5)

        # Sorting
        if sort_by == "oldest":
            query += " ORDER BY n.published_at ASC"
        elif sort_by == "expiring_soon":
            query += " ORDER BY CASE WHEN n.valid_to IS NULL THEN 1 ELSE 0 END, n.valid_to ASC"
        else:
            query += " ORDER BY CASE WHEN n.status = 'active' THEN 0 WHEN n.status = 'upcoming' THEN 1 ELSE 2 END, n.published_at DESC"

        cur.execute(query, params)
        raw_rows = cur.fetchall()

        # Enrich notices with routes and stations
        notices = []
        for r in raw_rows:
            nid = r["notice_id"]
            cur.execute("SELECT route_id FROM notice_routes WHERE notice_id = ?", (nid,))
            routes = [row[0] for row in cur.fetchall()]

            cur.execute("SELECT station FROM notice_stations WHERE notice_id = ?", (nid,))
            stations = [row[0] for row in cur.fetchall()]

            item = dict(r)
            item["routes"] = routes if routes else [r["route_id"]]
            item["stations"] = stations
            item["valid_from_ist"] = format_ist_datetime(r["valid_from"])
            item["valid_to_ist"] = format_ist_datetime(r["valid_to"])
            item["checked_relative"] = format_relative_time(r["last_confirmed_at"])
            notices.append(item)

        # Compute dynamic facets exclusively from matching notices
        facet_op_types = {}
        facet_agencies = {}
        facet_routes = {}
        facet_stations = {}
        facet_areas = {}
        facet_types = {}
        facet_statuses = {}
        facet_years = {}

        for n in notices:
            op = n.get("operator_type", "Government")
            facet_op_types[op] = facet_op_types.get(op, 0) + 1

            ag = n.get("agency", "")
            facet_agencies[ag] = facet_agencies.get(ag, 0) + 1

            for rt in n.get("routes", []):
                facet_routes[rt] = facet_routes.get(rt, 0) + 1

            for st in n.get("stations", []):
                facet_stations[st] = facet_stations.get(st, 0) + 1

            ar = n.get("area", "")
            facet_areas[ar] = facet_areas.get(ar, 0) + 1

            tp = n.get("type", "")
            facet_types[tp] = facet_types.get(tp, 0) + 1

            st_val = n.get("status", "")
            facet_statuses[st_val] = facet_statuses.get(st_val, 0) + 1

            pub = n.get("published_at", "")
            if len(pub) >= 4:
                y = pub[:4]
                facet_years[y] = facet_years.get(y, 0) + 1

        # Sources summary for header
        cur.execute("SELECT source_key, agency, operator_type, label, last_success_at, consecutive_failures, last_error FROM sources WHERE enabled = 1")
        sources_rows = cur.fetchall()
        sources_summary = []
        for s in sources_rows:
            fails = s["consecutive_failures"]
            state = "error" if fails > 0 else "up to date"
            color = "emerald-400" if state == "up to date" else "rose-400"
            sources_summary.append({
                "source_key": s["source_key"],
                "agency": s["agency"],
                "operator_type": s["operator_type"],
                "label": s["label"],
                "state": state,
                "dot_color": color,
                "last_confirmed_relative": format_relative_time(s["last_success_at"]),
                "consecutive_failures": fails
            })

    return jsonify({
        "total": len(notices),
        "notices": notices,
        "facets": {
            "operator_types": facet_op_types,
            "agencies": facet_agencies,
            "routes": facet_routes,
            "stations": facet_stations,
            "areas": facet_areas,
            "types": facet_types,
            "statuses": facet_statuses,
            "years": facet_years
        },
        "sources_summary": sources_summary
    })

@app.route("/api/notices/<path:notice_id>", methods=["GET"])
def get_notice_detail(notice_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT n.*, s.operator_type, s.label as source_label
            FROM notices n
            JOIN sources s ON n.source_id = s.source_id
            WHERE n.notice_id = ?
        """, (notice_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Notice not found"}), 404

        notice = dict(row)

        cur.execute("SELECT route_id FROM notice_routes WHERE notice_id = ?", (notice_id,))
        notice["routes"] = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT station FROM notice_stations WHERE notice_id = ?", (notice_id,))
        notice["stations"] = [s[0] for s in cur.fetchall()]

        notice["valid_from_ist"] = format_ist_datetime(notice["valid_from"])
        notice["valid_to_ist"] = format_ist_datetime(notice["valid_to"])
        notice["checked_relative"] = format_relative_time(notice["last_confirmed_at"])

        # Fetch revisions
        cur.execute("SELECT * FROM notice_revisions WHERE notice_id = ? ORDER BY revision_id DESC", (notice_id,))
        rev_rows = cur.fetchall()
        revisions = []
        for rev in rev_rows:
            r = dict(rev)
            r["changed_at_ist"] = format_ist_datetime(r["changed_at"])
            r["valid_from_ist"] = format_ist_datetime(r["valid_from"])
            r["valid_to_ist"] = format_ist_datetime(r["valid_to"])
            revisions.append(r)

        notice["revisions"] = revisions
        return jsonify(notice)

@app.route("/api/alerts/options", methods=["GET"])
def get_alert_options():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT agency FROM notices ORDER BY agency")
        agencies = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT route_id FROM notice_routes ORDER BY route_id")
        routes = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT station FROM notice_stations ORDER BY station")
        stations = [s[0] for s in cur.fetchall()]

        cur.execute("SELECT DISTINCT area FROM notices ORDER BY area")
        areas = [a[0] for a in cur.fetchall()]

        cur.execute("SELECT DISTINCT type FROM notices ORDER BY type")
        types = [t[0] for t in cur.fetchall()]

    return jsonify({
        "agencies": agencies,
        "routes": routes,
        "stations": stations,
        "areas": areas,
        "types": types
    })

@app.route("/api/alerts/subscribe", methods=["POST"])
def handle_subscribe():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email address is required"}), 400

    filters = {
        "routes": data.get("routes", []),
        "stations": data.get("stations", []),
        "areas": data.get("areas", []),
        "types": data.get("types", [])
    }

    with get_db() as conn:
        sub_id = subscribe_user(conn, email, filters)
        # Log past active notices for this subscriber
        cur = conn.cursor()
        cur.execute("SELECT notice_id, revision_id FROM notices WHERE status = 'active'")
        active_notices = cur.fetchall()
        for an in active_notices:
            cur.execute(
                """
                INSERT OR IGNORE INTO alert_log (notice_id, revision_id, subscriber_id, alert_status, alerted_at)
                VALUES (?, ?, ?, 'sent', ?)
                """,
                (an[0], an[1], sub_id, datetime.now(IST_TIMEZONE).isoformat())
            )

    return jsonify({"ok": True, "message": "Subscription preferences saved successfully", "subscriber_id": sub_id})

@app.route("/api/sources", methods=["GET"])
def get_sources():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM notices WHERE source_id = s.source_id) as total_notices,
                   (SELECT COUNT(*) FROM notices WHERE source_id = s.source_id AND status = 'active') as active_notices
            FROM sources s
            ORDER BY s.source_id ASC
        """)
        source_rows = cur.fetchall()
        sources = []
        for s in source_rows:
            d = dict(s)
            d["last_attempt_relative"] = format_relative_time(s["last_attempt_at"])
            d["last_success_relative"] = format_relative_time(s["last_success_at"])
            d["state"] = "ERROR" if s["consecutive_failures"] > 0 else "LIVE"
            sources.append(d)

        cur.execute("""
            SELECT fr.*, s.label as source_label
            FROM fetch_runs fr
            JOIN sources s ON fr.source_id = s.source_id
            ORDER BY fr.started_at DESC
            LIMIT 25
        """)
        runs_rows = cur.fetchall()
        runs = [dict(r) for r in runs_rows]

    return jsonify({
        "sources": sources,
        "recent_runs": runs
    })

@app.route("/api/admin/refresh", methods=["POST"])
def admin_refresh():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    # Also allow simple query or header
    if token != ADMIN_TOKEN and request.args.get("token") != ADMIN_TOKEN:
        # In development allow refresh if local request
        if not (request.remote_addr in ("127.0.0.1", "::1")):
            return jsonify({"error": "Unauthorized"}), 401

    with get_db() as conn:
        results = sync_engine.sync_all(conn)

    return jsonify({"ok": True, "results": results})

@app.route("/favicon.ico")
def favicon():
    """Explicitly returns 204 No Content so browsers never display or cache a favicon."""
    return Response(status=204, mimetype="image/x-icon")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api") or path.startswith("demo-source"):
        return jsonify({"error": "Not found"}), 404
    if FRONTEND_DIST.exists():
        target = FRONTEND_DIST / path
        if path and target.exists() and target.is_file():
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "TransitNotice Tamil Nadu Backend API running. Run Vite frontend on http://127.0.0.1:3000."}), 200

# ==============================================================================
# BACKGROUND WORKER & BOOTSTRAP
# ==============================================================================

def background_sync_worker():
    while True:
        try:
            with get_db() as conn:
                sync_engine.sync_all(conn)
        except Exception as e:
            logger.error(f"Background worker sync error: {e}")
        time.sleep(60)

def start_background_worker():
    thread = threading.Thread(target=background_sync_worker, daemon=True)
    thread.start()

# Initialize database
with app.app_context():
    init_db()

def deferred_startup_sync():
    """Waits for Flask HTTP socket to be active, then seeds initial scrape."""
    time.sleep(1.0)
    try:
        with get_db() as conn:
            sync_engine.sync_all(conn)
    except Exception as e:
        logger.warning(f"Initial sync note: {e}")

if __name__ == "__main__":
    threading.Thread(target=deferred_startup_sync, daemon=True).start()
    start_background_worker()
    print(f" * TransitNotice Flask Backend running on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
