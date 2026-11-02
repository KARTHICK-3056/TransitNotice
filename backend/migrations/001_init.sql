-- Migration 001: TransitNotice 8-Table Core Schema for Tamil Nadu

CREATE TABLE IF NOT EXISTS sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key TEXT UNIQUE NOT NULL,
    agency TEXT NOT NULL,
    operator_type TEXT NOT NULL CHECK(operator_type IN ('Government', 'Private')),
    base_url TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    refresh_seconds INTEGER NOT NULL DEFAULT 300,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_attempt_at TEXT,
    last_success_at TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    next_run_at TEXT,
    last_error TEXT,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notices (
    notice_id TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    agency TEXT NOT NULL,
    route_id TEXT NOT NULL,
    area TEXT NOT NULL,
    source_url TEXT NOT NULL,
    type TEXT NOT NULL,
    summary TEXT NOT NULL,
    published_at TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    status TEXT NOT NULL CHECK(status IN ('active', 'upcoming', 'ended', 'withdrawn', 'cancelled')),
    observed_at TEXT NOT NULL,
    last_confirmed_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    revision_id INTEGER NOT NULL DEFAULT 1,
    change_summary TEXT,
    subscriber_filter TEXT,
    alert_status TEXT,
    alerted_at TEXT,
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    UNIQUE(source_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_notices_status ON notices(status);
CREATE INDEX IF NOT EXISTS idx_notices_agency ON notices(agency);
CREATE INDEX IF NOT EXISTS idx_notices_valid_window ON notices(valid_from, valid_to);

CREATE TABLE IF NOT EXISTS notice_routes (
    notice_id TEXT NOT NULL REFERENCES notices(notice_id) ON DELETE CASCADE,
    route_id TEXT NOT NULL,
    PRIMARY KEY (notice_id, route_id)
);

CREATE TABLE IF NOT EXISTS notice_stations (
    notice_id TEXT NOT NULL REFERENCES notices(notice_id) ON DELETE CASCADE,
    station TEXT NOT NULL,
    PRIMARY KEY (notice_id, station)
);

CREATE TABLE IF NOT EXISTS notice_revisions (
    notice_id TEXT NOT NULL REFERENCES notices(notice_id) ON DELETE CASCADE,
    revision_id INTEGER NOT NULL,
    changed_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    status TEXT NOT NULL,
    route_id TEXT NOT NULL,
    area TEXT NOT NULL,
    change_summary TEXT,
    PRIMARY KEY (notice_id, revision_id)
);

CREATE TABLE IF NOT EXISTS fetch_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    outcome TEXT NOT NULL CHECK(outcome IN ('ok', 'error', 'blocked')),
    http_status INTEGER,
    items_parsed INTEGER NOT NULL DEFAULT 0,
    items_skipped INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    revised_count INTEGER NOT NULL DEFAULT 0,
    withdrawn_count INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_fetch_runs_source ON fetch_runs(source_id, started_at);

CREATE TABLE IF NOT EXISTS subscribers (
    subscriber_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    subscriber_filter TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_log (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    notice_id TEXT NOT NULL REFERENCES notices(notice_id) ON DELETE CASCADE,
    revision_id INTEGER NOT NULL,
    subscriber_id INTEGER NOT NULL REFERENCES subscribers(subscriber_id) ON DELETE CASCADE,
    alert_status TEXT NOT NULL,
    alerted_at TEXT NOT NULL,
    UNIQUE(notice_id, revision_id, subscriber_id)
);

