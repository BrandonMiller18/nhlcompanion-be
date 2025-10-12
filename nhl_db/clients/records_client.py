from typing import Any, Dict, List, Optional

import requests

from ..config import RECORDS_BASE


def fetch_franchises(session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    session = session or requests.Session()
    includes = (
        "include=teams.id&include=teams.active&include=teams.triCode&include=teams.placeName"
        "&include=teams.commonName&include=teams.fullName&include=teams.logos"
        "&include=teams.conference.name&include=teams.division.name"
        "&include=teams.franchiseTeam.firstSeason.id&include=teams.franchiseTeam.lastSeason.id"
        "&include=teams.franchiseTeam.teamCommonName"
    )
    url = f"{RECORDS_BASE}/franchise?{includes}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json() or {}
    return data.get("data", [])


