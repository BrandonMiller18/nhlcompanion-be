from typing import Any, Dict, List, Optional

import requests

from ..config import NHL_WEB_BASE


def fetch_roster(tricode: str, season: str, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    session = session or requests.Session()
    tri = (tricode or "").lower()
    url = f"{NHL_WEB_BASE}/roster/{tri}/{season}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json() or {}
    combined: List[Dict[str, Any]] = []
    for group in ("forwards", "defensemen", "goalies"):
        combined.extend(data.get(group, []) or [])
    return combined


def fetch_schedule_for_date(date_str: str, session: Optional[requests.Session] = None) -> List[Dict[str, Any]]:
    print(f"Fetching schedule for date: {date_str}...")
    session = session or requests.Session()
    url = f"{NHL_WEB_BASE}/schedule/{date_str}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json() or {}
    games: List[Dict[str, Any]] = []
    for day in data.get("gameWeek", []) or []:
        for g in day.get("games", []) or []:
            games.append(g)
    return games


def fetch_game_landing(game_id: int, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    session = session or requests.Session()
    url = f"{NHL_WEB_BASE}/gamecenter/{game_id}/landing"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


def fetch_game_boxscore(game_id: int, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    session = session or requests.Session()
    url = f"{NHL_WEB_BASE}/gamecenter/{game_id}/boxscore"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


def fetch_game_pbp(game_id: int, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    session = session or requests.Session()
    url = f"{NHL_WEB_BASE}/gamecenter/{game_id}/play-by-play"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


