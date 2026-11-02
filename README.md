# TransitNotice (WEB-07: Public Transport Service Update Tracker for Tamil Nadu)

TransitNotice is a full-stack public transport advisory intelligence system purpose-built for Tamil Nadu transit networks (Chennai Metro Rail Limited road diversions, CMRL press releases, intermodal metro services, and private intercity coach routes).

It utilizes a **clean decoupled architecture**:
1. **Backend:** Python Flask + SQLite JSON API engine implemented using **only Python standard-library scraping modules** (`urllib.request`, `urllib.robotparser`, `html.parser`, `xml.etree.ElementTree`, `zoneinfo`, `sqlite3`, `hashlib`, `threading`).
2. **Frontend:** Minimal, visually stunning React SPA (Vite + Tailwind CSS + Lucide React) with a Linear / Vercel-inspired dark-mode aesthetic.

---

## 1. Design & UI Philosophy

- **Aesthetic Theme:** Linear / Vercel-inspired dark-mode minimalism.
  - Page Canvas: `#0A0E14`
  - Elevated Containers & Cards: `#111722`
  - Hover States: `#161F2E`
  - Crisp Borders: `1px solid rgba(255, 255, 255, 0.07)` with hover illumination
  - Status Indicators: Glowing 6px translucent dots (`emerald-400` for "In effect now" / "LIVE", `amber-400` for "Withdrawn" / "Stale", `rose-400` for "Ended" / "Error", `sky-400` for notice types)
- **Strictly 4 Top Navbar Routes (No sidebars, no clutter):**
  1. `Current notices` (`/`)
  2. `Ended notices` (`/ended`)
  3. `Get alerts` (`/alerts`)
  4. `Data sources` (`/sources`)
  Plus Notice Detail view (`/notices/:noticeId`).

---

## 2. Real Tamil Nadu Sources & Scraper Engine

Built using **only Python standard library** network and parser modules:
1. **CMRL Road Diversions (`cmrl` - Government, Live):**
   - Ingests `https://chennaimetrorail.org/wp-json/wp/v2/road-diversion` and parses individual diversion HTML pages using standard `html.parser` to extract Corridor packages (Corridors 3, 4, 5), stations, diversion start dates, and last updated timestamps. Detail pages are cached until modified.
2. **CMRL Press Releases (`cmrl_press` - Government, Live):**
   - Scrapes `https://chennaimetrorail.org/press-release/` HTML table using `html.parser`. Filters passenger advisories (gate closures, parking suspensions, revised holiday timings, special match services) from corporate news. Matches stations against CMRL lines (Blue Line, Green Line, Corridors 3, 4, 5).
3. **Sample Chennai Transit (`sample_metro` - Demo Agency):**
   - Served at `/demo-source/metro` (HTML) with realistic notices for live mentor testing (extend outage by 24h, open-ended notices without end date).
4. **Sample Private Coaches (`demo_private_bus` - Demo Operator):**
   - Served at `/demo-source/private_coaches.xml` (RSS) with 4 Tamil Nadu intercity bus routes (Chennai - Coimbatore, Chennai - Madurai, Chennai - Trichy, Chennai - Tirunelveli) parsed using `xml.etree.ElementTree`. Demonstrates `operator_type: Private`.

---

## 3. Exact 8-Table SQLite Schema (`migrations/001_init.sql`)

1. `sources`: Source metadata, base URLs, timezone (`Asia/Kolkata`), refresh intervals, consecutive failure counts, and last error logs.
2. `notices`: Unique notices keyed deterministically by `source_key:external_id`, storing agency, routes, area, type, summary, published date, valid window (nullable `valid_to` for open-ended), status (`active`, `upcoming`, `ended`, `withdrawn`, `cancelled`), observed/last confirmed timestamps, SHA-256 hash, and revision ID.
3. `notice_routes`: Normalized many-to-one junction linking notices to affected routes (`PK(notice_id, route_id)`).
4. `notice_stations`: Normalized junction mapping notices to specific stations (`PK(notice_id, station)`).
5. `notice_revisions`: Snapshot table tracking historical versions, previous hashes, and human-readable diffs whenever a notice is modified.
6. `fetch_runs`: Audit trail tracking each scraper run, timestamp, outcome (`ok`, `error`, `blocked`), HTTP response code, yields, and diagnostics.
7. `subscribers`: Email addresses and JSON preference filters.
8. `alert_log`: Log of dispatched alerts with unique constraint `UNIQUE(notice_id, revision_id, subscriber_id)` guaranteeing zero duplicates.

---

## 4. Quickstart & Launch Instructions

### Option A: One-Click Startup (Windows)
Double-click or run:
```cmd
start.bat
```
This automatically verifies dependencies, initializes the database, builds the frontend bundle, and boots the application on `http://127.0.0.1:5000/`.

### Option B: Manual Launch

1. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python -c "from backend.db import init_db; init_db()"
   ```

3. **Build or run frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Launch Flask backend:**
   ```bash
   python -m backend.app
   ```
   Navigate to `http://127.0.0.1:5000/`.

---

## 5. Automated Acceptance Test Suite

Run the full `unittest` test suite verifying all WEB-07 core acceptance criteria:
```bash
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Verified test cases:
1. `test_1_expired_notice_never_marked_active`: Expired notices (`valid_to` in past) are computed as `ended` and never `active`.
2. `test_2_multi_route_filtering`: Notices affecting multiple lines (e.g., `Blue Line, Green Line`) accurately match queries for both routes.
3. `test_3_extended_outage_bumps_revision_and_change_summary`: +24h date extension increments `revision_id` to 2 and appends human-readable diff to revision history.
4. `test_4_ist_datetime_and_open_ended_support`: Open-ended notices (`valid_to = NULL`) parse cleanly and display as `ACTIVE (Until Further Notice)`.
5. `test_5_source_outage_503_preserves_last_confirmed_at`: Upstream 503 errors freeze `last_confirmed_at`, preserving provenance without falsifying live status.
6. `test_6_single_alert_deduplication`: Unique constraint `UNIQUE(notice_id, revision_id, subscriber_id)` guarantees at most 1 alert per revision.

---

## 6. Live Mentor Challenge Simulator Guide

A dedicated **Mentor Evaluation Panel** is integrated into the bottom of the dashboard:
- **+24h Outage Extension:** Mutates `/demo-source/metro` notice `METRO-DEMO-01`, re-syncs, increments `revision_id` to 2, logs *"Extended valid_to by 24 hours"* in Revision History, and dispatches an alert.
- **Inject Open-Ended Notice:** Adds an advisory with `valid_to = NULL`, displayed as `In effect now` with `– no end date announced (until further notice)`.
- **Simulate 503 Outage:** Forces the demo endpoint to return HTTP 503. The header and Sources view flag the source as `ERROR`, while all previously confirmed timestamps remain frozen.
- **Recover (200 OK):** Restores the demo endpoint to normal healthy status.
- **Reset Demo Fixtures:** Restores baseline fixture records.
