import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from backend.sources.base import BaseSourceAdapter, Fetcher

logger = logging.getLogger("transitnotice.demo_private_bus")

PRIVATE_BUS_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:transit="http://transitnotice.local/ns">
  <channel>
    <title>Tamil Nadu Private Intercity Coach Updates</title>
    <link>http://127.0.0.1:5000/demo-source/private_coaches.xml</link>
    <description>Service updates for private luxury sleeper and AC omnibus services</description>
    
    <item>
      <guid>PVT-COACH-101</guid>
      <title>Chennai - Coimbatore Night Sleeper Diversion via Salem Bypass</title>
      <description>Bridge repair work on NH544 between Sankari and Bhavani. All private omnibus services rerouted via Salem Outer Ring Road with 30-minute delay expected.</description>
      <category>Diversion</category>
      <transit:route>Chennai - Coimbatore</transit:route>
      <transit:stations>Koyambedu Omnigus Bus Stand, Salem Bypass, Bhavani, Gandhipuram</transit:stations>
      <transit:area>Western Corridor (NH544)</transit:area>
      <pubDate>2026-03-20T10:00:00Z</pubDate>
      <transit:validFrom>2026-03-20T18:00:00</transit:validFrom>
      <transit:validTo>2026-03-25T06:00:00</transit:validTo>
      <link>http://127.0.0.1:5000/demo-source/private_coaches.xml#PVT-COACH-101</link>
    </item>

    <item>
      <guid>PVT-COACH-102</guid>
      <title>Chennai - Madurai Semi-Sleeper Rescheduled Boarding at Kilambakkam (KCBT)</title>
      <description>Boarding point for all Southern Tamil Nadu intercity private services consolidated strictly to Kilambakkam Bus Terminus. CMBT boarding discontinued.</description>
      <category>Revised timings</category>
      <transit:route>Chennai - Madurai</transit:route>
      <transit:stations>Kilambakkam KCBT, Villupuram, Trichy Tollgate, Mattuthavani</transit:stations>
      <transit:area>Southern Corridor (NH45)</transit:area>
      <pubDate>2026-03-15T08:00:00Z</pubDate>
      <transit:validFrom>2026-03-15T00:00:00</transit:validFrom>
      <transit:validTo>2026-04-30T23:59:59</transit:validTo>
      <link>http://127.0.0.1:5000/demo-source/private_coaches.xml#PVT-COACH-102</link>
    </item>

    <item>
      <guid>PVT-COACH-103</guid>
      <title>Chennai - Trichy Express Services: Single-Lane Toll Plaza Bottleneck</title>
      <description>Ulundurpet Toll Plaza lane maintenance causing 20-30 min slow-moving traffic on Friday and Sunday evening departures.</description>
      <category>Delays expected</category>
      <transit:route>Chennai - Trichy</transit:route>
      <transit:stations>Kilambakkam, Tindivanam, Villupuram, Ulundurpet, Central Bus Stand Trichy</transit:stations>
      <transit:area>Central Corridor (NH38)</transit:area>
      <pubDate>2026-03-18T09:00:00Z</pubDate>
      <transit:validFrom>2026-03-18T00:00:00</transit:validFrom>
      <transit:validTo>2026-03-26T23:59:59</transit:validTo>
      <link>http://127.0.0.1:5000/demo-source/private_coaches.xml#PVT-COACH-103</link>
    </item>

    <item>
      <guid>PVT-COACH-104</guid>
      <title>Chennai - Tirunelveli Super Deluxe: Open-Ended Detour via Madurai Ring Road</title>
      <description>Madurai Ring Road flyover expansion. Intercity buses bypassing city entry, boarding restricted to bypass toll plaza until further notice.</description>
      <category>Diversion</category>
      <transit:route>Chennai - Tirunelveli</transit:route>
      <transit:stations>Kilambakkam, Madurai Ring Road, Virudhunagar, Tirunelveli Junction</transit:stations>
      <transit:area>Deep South Corridor (NH44)</transit:area>
      <pubDate>2026-03-01T08:00:00Z</pubDate>
      <transit:validFrom>2026-03-01T08:00:00</transit:validFrom>
      <transit:validTo></transit:validTo>
      <link>http://127.0.0.1:5000/demo-source/private_coaches.xml#PVT-COACH-104</link>
    </item>
  </channel>
</rss>
"""

class DemoPrivateBusAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            source_key="demo_private_bus",
            label="Sample Private Coaches (demo operator)",
            agency="Sample Private Coaches (demo operator)",
            operator_type="Private",
            base_url="http://127.0.0.1:5000/demo-source/private_coaches.xml"
        )

    def fetch_notices(self, fetcher: Fetcher) -> List[Dict[str, Any]]:
        try:
            xml_text = fetcher.fetch_url(self.base_url)
        except Exception:
            xml_text = PRIVATE_BUS_RSS_XML
        root = ET.fromstring(xml_text)

        channel = root.find("channel")
        if channel is None:
            return []

        ns = {"transit": "http://transitnotice.local/ns"}
        notices = []

        for item in channel.findall("item"):
            guid = item.find("guid").text if item.find("guid") is not None else ""
            title = item.find("title").text if item.find("title") is not None else ""
            desc = item.find("description").text if item.find("description") is not None else ""
            cat = item.find("category").text if item.find("category") is not None else "General notice"
            link = item.find("link").text if item.find("link") is not None else f"{self.base_url}#{guid}"

            route_el = item.find("transit:route", ns)
            route = route_el.text.strip() if route_el is not None and route_el.text else "Intercity"

            stations_el = item.find("transit:stations", ns)
            if stations_el is not None and stations_el.text:
                stations = [s.strip() for s in stations_el.text.split(",") if s.strip()]
            else:
                stations = [route]

            area_el = item.find("transit:area", ns)
            area = area_el.text.strip() if area_el is not None and area_el.text else f"Tamil Nadu - {route}"

            valid_from_el = item.find("transit:validFrom", ns)
            valid_from = valid_from_el.text.strip() if valid_from_el is not None and valid_from_el.text else "2026-03-20T00:00:00"

            valid_to_el = item.find("transit:validTo", ns)
            valid_to = valid_to_el.text.strip() if valid_to_el is not None and valid_to_el.text else None

            notices.append({
                "external_id": guid,
                "agency": self.agency,
                "operator_type": self.operator_type,
                "route_id": route,
                "routes": [route],
                "stations": stations,
                "area": area,
                "source_url": link,
                "type": cat,
                "summary": f"{title} - {desc}" if title not in desc else desc,
                "published_at": valid_from,
                "valid_from": valid_from,
                "valid_to": valid_to,
            })

        return notices

