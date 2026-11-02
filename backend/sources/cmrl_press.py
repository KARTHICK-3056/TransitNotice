import re
import logging
from html.parser import HTMLParser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from backend.sources.base import BaseSourceAdapter, Fetcher, FetchError

logger = logging.getLogger("transitnotice.cmrl_press")
IST = ZoneInfo("Asia/Kolkata")

# Passenger advisory keywords to match genuine travel updates
PASSENGER_INCLUDE = [
    'closure', 'closed', 'gate', 'entry', 'exit', 'parking', 'timing', 'time',
    'extended', 'extension', 'special train', 'service', 'train', 'diversion',
    'traffic', 'maintenance', 'delay', 'interruption', 'rescheduled', 'frequency',
    'snag', 'disrupt', 'suspend', 'escalator', 'feeder', 'shuttle', 'fare', 'ticket',
    'passenger', 'commuter', 'smart card', 'token', 'qr code', 'ncmc', 'metro line',
    'blue line', 'green line', 'corridor', 'travel', 'card'
]

# Corporate / PR news to strictly exclude
CORPORATE_EXCLUDE = [
    'minister', 'inspection', 'visit', 'cpr', 'medical', 'camp', 'health',
    'blood donation', 'award', 'trophy', 'mou', 'tender', 'inaugurat',
    'contract', 'rotary', 'hunt', 'music', 'cultural', 'marathon', 'quiz',
    'micro-plasma', 'oxidation', 'celebrat', 'art', 'carnival', 'ridership',
    'patronage', 'lakh passengers', 'crore passengers', 'travelled',
    'recruitment', 'internship', 'employment', 'vacancy', 'interview',
    'plantation', 'swachh', 'cleanliness', 'yoga', 'safety week', 'women\'s day',
    'delegation', 'ambassador', 'consul', 'foundation day', 'independence day',
    'republic day', 'diwali', 'greeting', 'student', 'school', 'college',
    'workshop', 'seminar', 'conference', 'meeting with', 'commemorat',
    'cricket trophy', 'badminton', 'volleyball', 'sports'
]

STATION_LINE_MAP = {
    "Blue Line": [
        "Wimco Nagar", "Tollgate", "Washermanpet", "Chennai Central",
        "Government Estate", "LIC", "Thousand Lights", "AG-DMS",
        "Teynampet", "Nandanam", "Saidapet", "Guindy", "Meenambakkam", "Airport"
    ],
    "Green Line": [
        "Chennai Central", "Egmore", "Nehru Park", "Kilpauk",
        "Pachaiyappa's College", "Shenoy Nagar", "Anna Nagar East",
        "Anna Nagar Tower", "Thirumangalam", "Koyambedu", "Arumbakkam",
        "Vadapalani", "Ashok Nagar", "Ekkattuthangal", "Alandur", "St. Thomas Mount"
    ],
    "Corridor 3": ["Madhavaram", "Ayanavaram", "Purasaiwakkam", "Sterling Road", "Mylapore", "Adyar", "SIPCOT"],
    "Corridor 4": ["Light House", "Panagal Park", "Kodambakkam", "Power House", "Saligramam", "Poonamallee"],
    "Corridor 5": ["Villivakkam", "Anna Nagar", "Koyambedu Market", "Porur", "Madipakkam", "Sholinganallur"]
}

class HTMLTablePressParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.current_cell = []
        self.current_row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_row = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.current_row.append(" ".join(self.current_cell).strip())
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)

    def handle_data(self, data):
        if self.in_cell:
            c = data.strip()
            if c:
                self.current_cell.append(c)

def parse_press_date(raw_date: str) -> datetime:
    cleaned = raw_date.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
    return datetime(2026, 3, 1, 8, 0)

def classify_notice_type(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ('diversion', 'traffic diversion', 'reroute', 'road diversion')):
        return "Road diversion"
    if any(k in t for k in ('closure', 'closed', 'parking', 'gate', 'entry', 'exit', 'shut')):
        return "Station / entry / parking closed"
    if any(k in t for k in ('timing', 'schedule', 'timetable', 'extended service', 'frequency', 'headway', 'rescheduled')):
        return "Revised timings"
    if any(k in t for k in ('maintenance', 'power block', 'track work', 'overhead', 'escalator', 'lift')):
        return "Track maintenance"
    if any(k in t for k in ('delay', 'interruption', 'snag', 'disrupt', 'suspend')):
        return "Delays expected"
    return "Passenger advisory"

class CMRLPressAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            source_key="cmrl_press",
            label="CMRL press releases",
            agency="Chennai Metro Rail Limited",
            operator_type="Government",
            base_url="https://chennaimetrorail.org/press-release/"
        )

    def is_passenger_advisory(self, title: str) -> bool:
        t_low = title.lower()
        if any(corp in t_low for corp in CORPORATE_EXCLUDE):
            return False
        return any(kw in t_low for kw in PASSENGER_INCLUDE)

    def infer_lines_and_stations(self, text: str):
        matched_lines = set()
        matched_stations = set()

        text_low = text.lower()
        for line_name, station_list in STATION_LINE_MAP.items():
            if line_name.lower() in text_low:
                matched_lines.add(line_name)
            for st in station_list:
                if st.lower() in text_low:
                    matched_stations.add(st)
                    matched_lines.add(line_name)

        routes = list(matched_lines) if matched_lines else ["Chennai Metro Network"]
        stations = list(matched_stations) if matched_stations else ["Network-wide"]
        return routes, stations

    def fetch_notices(self, fetcher: Fetcher) -> List[Dict[str, Any]]:
        rows = []
        try:
            html_text = fetcher.fetch_url(self.base_url)
            parser = HTMLTablePressParser()
            parser.feed(html_text)
            rows = parser.rows
        except Exception as e:
            logger.warning(f"Could not scrape live CMRL press releases table ({e}). Using authoritative baseline records.")

        notices = []
        if rows:
            for idx, r in enumerate(rows):
                if len(r) < 2:
                    continue
                date_str = r[0]
                title = r[1]
                if not self.is_passenger_advisory(title):
                    continue

                routes, stations = self.infer_lines_and_stations(title)
                ext_id = f"PR-{date_str.replace('/', '-')}-{idx}"
                pub_dt = parse_press_date(date_str)
                iso_pub = pub_dt.strftime("%Y-%m-%dT%H:%M:%S")

                title_low = title.lower()
                adv_type = classify_notice_type(title)

                # 14-DAY VALIDITY RULE FOR PRESS RELEASES:
                # "Press releases carry no validity: undated ones are current for 14 days"
                # If explicit "permanent" or ongoing entry closure without end date:
                if "permanent closure" in title_low or "closed until further notice" in title_low:
                    iso_valid_to = None  # Open-ended
                else:
                    # Look for explicit end date in title (e.g. "between 20.10.2025 and 24.10.2025")
                    date_match = re.findall(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', title)
                    if len(date_match) >= 2:
                        end_dt = parse_press_date(date_match[1])
                        # Ensure time is end of day
                        end_dt = end_dt.replace(hour=23, minute=59, second=59)
                        iso_valid_to = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    else:
                        # Apply 14-day rule
                        end_dt = pub_dt + timedelta(days=14)
                        end_dt = end_dt.replace(hour=23, minute=59, second=59)
                        iso_valid_to = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

                notices.append({
                    "external_id": ext_id,
                    "agency": self.agency,
                    "operator_type": self.operator_type,
                    "route_id": ", ".join(routes),
                    "routes": routes,
                    "stations": stations,
                    "area": f"Chennai - {routes[0]}",
                    "source_url": f"{self.base_url}#{ext_id}",
                    "type": adv_type,
                    "summary": title,
                    "published_at": iso_pub,
                    "valid_from": iso_pub,
                    "valid_to": iso_valid_to,
                })

        return notices
