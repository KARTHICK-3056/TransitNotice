import copy
import logging
from html.parser import HTMLParser
from typing import List, Dict, Any
from backend.sources.base import BaseSourceAdapter, Fetcher, FetchError

logger = logging.getLogger("transitnotice.sample_metro")

DEFAULT_METRO_DEMO_NOTICES = [
    {
        "id": "METRO-DEMO-01",
        "title": "Overhead Line Inspection between Koyambedu and Alandur",
        "route": "Green Line",
        "stations": ["Koyambedu", "Arumbakkam", "Vadapalani", "Ashok Nagar", "Ekkattuthangal", "Alandur"],
        "area": "Chennai - Green Line",
        "type": "Track maintenance",
        "summary": "Scheduled overnight electrical overhead line inspection. Trains operating at 15-minute intervals instead of 7-minute peak headways.",
        "published_at": "2026-03-20T06:00:00",
        "valid_from": "2026-03-20T06:00:00",
        "valid_to": "2026-03-22T18:00:00",  # Can be extended +24h by mentor
        "link": "/demo-source/metro#METRO-DEMO-01"
    },
    {
        "id": "METRO-DEMO-02",
        "title": "Underground Tunnel Signaling Upgrade on Blue Line Corridor",
        "route": "Blue Line",
        "stations": ["Chennai Central", "Government Estate", "LIC", "Thousand Lights", "AG-DMS"],
        "area": "Chennai - Blue Line",
        "type": "Delays expected",
        "summary": "Signaling system software calibration underway between Central and AG-DMS. Speeds capped at 40 km/h with 5-8 min minor delays.",
        "published_at": "2026-03-19T08:00:00",
        "valid_from": "2026-03-19T08:00:00",
        "valid_to": "2026-03-24T23:59:59",
        "link": "/demo-source/metro#METRO-DEMO-02"
    },
    {
        "id": "METRO-DEMO-03",
        "title": "Escalator Modernization at Airport Metro Concourse",
        "route": "Blue Line",
        "stations": ["Airport"],
        "area": "Chennai - Blue Line",
        "type": "Station / entry / parking closed",
        "summary": "Airport Metro terminal escalator 3 undergoing motor replacement. Passenger lifts operational. Expected completion mid-April.",
        "published_at": "2026-03-01T08:00:00",
        "valid_from": "2026-03-01T08:00:00",
        "valid_to": None,  # Open-ended
        "link": "/demo-source/metro#METRO-DEMO-03"
    },
    {
        "id": "METRO-DEMO-04",
        "title": "Completed Track Realignment at St. Thomas Mount Intermodal Hub",
        "route": "Green Line",
        "stations": ["St. Thomas Mount", "Alandur"],
        "area": "Chennai - Green Line",
        "type": "Track maintenance",
        "summary": "Track geometry adjustments completed. Full normal speed restored across all crossover switches.",
        "published_at": "2026-02-10T08:00:00",
        "valid_from": "2026-02-10T08:00:00",
        "valid_to": "2026-02-15T18:00:00",  # Expired / Ended
        "link": "/demo-source/metro#METRO-DEMO-04"
    }
]

class MetroDemoState:
    def __init__(self):
        self.notices = copy.deepcopy(DEFAULT_METRO_DEMO_NOTICES)
        self.simulate_503 = False
        self.log = ["Initialized demo metro feed with 4 notices"]

    def reset(self):
        self.notices = copy.deepcopy(DEFAULT_METRO_DEMO_NOTICES)
        self.simulate_503 = False
        self.log.append("Reset demo metro state to baseline fixtures")

    def extend_24h(self, notice_id="METRO-DEMO-01"):
        for n in self.notices:
            if n["id"] == notice_id:
                if n["valid_to"]:
                    # Add 24h
                    from datetime import datetime, timedelta
                    dt = datetime.fromisoformat(n["valid_to"])
                    new_dt = dt + timedelta(days=1)
                    n["valid_to"] = new_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    msg = f"Extended valid_to for {notice_id} by +24h to {n['valid_to']}"
                    self.log.append(msg)
                    return {"ok": True, "message": msg, "notice": n}
        return {"ok": False, "message": f"{notice_id} not found or no end date"}

    def inject_open_ended(self):
        new_id = f"METRO-DEMO-{len(self.notices) + 1:02d}"
        notice = {
            "id": new_id,
            "title": "Emergency Track Switch Calibration at Alandur Junction",
            "route": "Blue Line, Green Line",
            "stations": ["Alandur", "Guindy", "Ekkattuthangal"],
            "area": "Chennai - Intermodal Interchange",
            "type": "Delays expected",
            "summary": "Switch point inspection following overnight heavy rains. Trains crossing junction restricted to 25 km/h until further notice.",
            "published_at": "2026-03-21T07:00:00",
            "valid_from": "2026-03-21T07:00:00",
            "valid_to": None,  # Open-ended
            "link": f"/demo-source/metro#{new_id}"
        }
        self.notices.append(notice)
        msg = f"Injected open-ended notice {new_id} without end date"
        self.log.append(msg)
        return {"ok": True, "message": msg, "notice": notice}

    def set_503(self, enabled=True):
        self.simulate_503 = enabled
        msg = "Simulating HTTP 503 outage on demo source" if enabled else "Restored HTTP 200 on demo source"
        self.log.append(msg)
        return {"ok": True, "simulate_503": self.simulate_503, "message": msg}

metro_demo_state = MetroDemoState()

class DemoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.notices = []
        self.in_card = False
        self.cur_id = ""
        self.cur_tag = ""
        self.cur_data = {}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "div" and "data-id" in attr_dict:
            self.in_card = True
            self.cur_id = attr_dict["data-id"]
            self.cur_data = {"id": self.cur_id, "stations": []}
        elif self.in_card:
            self.cur_tag = attr_dict.get("class", tag)

    def handle_endtag(self, tag):
        if tag == "div" and self.in_card and self.cur_id:
            # card closed
            self.notices.append(self.cur_data)
            self.in_card = False
            self.cur_id = ""
            self.cur_tag = ""

    def handle_data(self, data):
        c = data.strip()
        if not c or not self.in_card:
            return
        if "title" in self.cur_tag:
            self.cur_data["title"] = c
        elif "route" in self.cur_tag:
            self.cur_data["route"] = c
        elif "station" in self.cur_tag:
            self.cur_data["stations"].append(c)
        elif "area" in self.cur_tag:
            self.cur_data["area"] = c
        elif "type" in self.cur_tag:
            self.cur_data["type"] = c
        elif "summary" in self.cur_tag:
            self.cur_data["summary"] = c
        elif "valid-from" in self.cur_tag:
            self.cur_data["valid_from"] = c
        elif "valid-to" in self.cur_tag:
            self.cur_data["valid_to"] = c if c != "None" else None

class SampleMetroAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            source_key="sample_metro",
            label="Sample Chennai Transit (demo agency)",
            agency="Sample Chennai Transit (demo agency)",
            operator_type="Government",
            base_url="http://127.0.0.1:5000/demo-source/metro"
        )

    def fetch_notices(self, fetcher: Fetcher) -> List[Dict[str, Any]]:
        # If fetcher encounters 503 or error, it will raise FetchError as required
        try:
            html_text = fetcher.fetch_url(self.base_url)
            parser = DemoHTMLParser()
            parser.feed(html_text)
            parsed_raw = parser.notices
        except FetchError as fe:
            if fe.status_code == 503 or metro_demo_state.simulate_503:
                raise
            parsed_raw = copy.deepcopy(metro_demo_state.notices)
        except Exception:
            if metro_demo_state.simulate_503:
                raise FetchError("503 Service Unavailable (Simulated by Mentor)", status_code=503)
            parsed_raw = copy.deepcopy(metro_demo_state.notices)

        notices = []
        for n in parsed_raw:
            routes = [r.strip() for r in n.get("route", "Metro").split(",")]
            notices.append({
                "external_id": n["id"],
                "agency": self.agency,
                "operator_type": self.operator_type,
                "route_id": n.get("route", "Metro"),
                "routes": routes,
                "stations": n.get("stations", []),
                "area": n.get("area", f"Chennai - {routes[0]}"),
                "source_url": f"{self.base_url}#{n['id']}",
                "type": n.get("type", "General notice"),
                "summary": n.get("summary", n.get("title", "")),
                "published_at": n.get("valid_from", "2026-03-20T06:00:00"),
                "valid_from": n.get("valid_from", "2026-03-20T06:00:00"),
                "valid_to": n.get("valid_to"),
            })
        return notices

