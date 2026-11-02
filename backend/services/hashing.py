import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

def normalize_string(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(str(s).strip().split())

def compute_content_hash(
    route_id: str,
    notice_type: str,
    summary: str,
    valid_from: Optional[str],
    valid_to: Optional[str]
) -> str:
    """
    Computes deterministic SHA-256 digest:
    route_id|type|summary|valid_from|valid_to
    """
    norm_route = normalize_string(route_id)
    norm_type = normalize_string(notice_type).lower()
    norm_summary = normalize_string(summary)
    norm_from = normalize_string(valid_from)
    norm_to = normalize_string(valid_to) or "OPEN_ENDED"

    raw = f"{norm_route}|{norm_type}|{norm_summary}|{norm_from}|{norm_to}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def generate_change_summary(old_notice: Dict[str, Any], new_notice: Dict[str, Any]) -> str:
    """Generates human-readable diff summary highlighting exact date extensions, route or summary changes."""
    changes = []

    old_to = old_notice.get("valid_to")
    new_to = new_notice.get("valid_to")

    if old_to != new_to:
        if old_to and new_to:
            try:
                dt_old = datetime.fromisoformat(old_to.replace("Z", ""))
                dt_new = datetime.fromisoformat(new_to.replace("Z", ""))
                diff_hours = (dt_new - dt_old).total_seconds() / 3600.0
                if diff_hours > 0:
                    h_val = int(diff_hours) if diff_hours.is_integer() else diff_hours
                    changes.append(f"Extended valid_to by {h_val} hours (until {new_to})")
                else:
                    changes.append(f"Adjusted valid_to to {new_to}")
            except Exception:
                changes.append(f"Valid to updated to {new_to}")
        elif old_to and not new_to:
            changes.append("Outage extended to open-ended (until further notice)")
        elif not old_to and new_to:
            changes.append(f"End date specified as {new_to}")

    old_routes = normalize_string(old_notice.get("route_id"))
    new_routes = normalize_string(new_notice.get("route_id"))
    if old_routes != new_routes:
        changes.append(f"Routes updated from [{old_routes}] to [{new_routes}]")

    old_summary = normalize_string(old_notice.get("summary"))
    new_summary = normalize_string(new_notice.get("summary"))
    if old_summary != new_summary:
        preview = new_summary[:50] + "..." if len(new_summary) > 50 else new_summary
        changes.append(f"Summary revised: '{preview}'")

    return "; ".join(changes) if changes else "Notice details refreshed"

