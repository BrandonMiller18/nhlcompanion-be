from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from datetime import datetime
import requests

from ..clients.nhl_web_client import fetch_game_boxscore, fetch_game_landing, fetch_game_pbp, fetch_schedule_for_date
from ..db import get_db_connection
from ..mappers.games import derive_game_fields_from_gamecenter, to_game_rows_from_schedule
from ..mappers.plays import map_play
from ..repositories.games_repo import (
    upsert_games_with_conn,
    update_game_fields_with_conn,
)
from ..repositories.plays_repo import upsert_plays_with_conn


def update_live_once(game_id: int) -> int:
    session = requests.Session()
    landing = fetch_game_landing(game_id, session=session)
    box = fetch_game_boxscore(game_id, session=session)
    pbp = fetch_game_pbp(game_id, session=session)

    game_state, period, clock, home_score, away_score, home_sog, away_sog = derive_game_fields_from_gamecenter(landing, box)
    conn = get_db_connection()
    try:
        update_game_fields_with_conn(conn, game_id, game_state, period, clock, home_score, away_score, home_sog, away_sog)

        plays = pbp.get("plays") or []
        rows = [map_play(game_id, p) for p in plays]
        count = upsert_plays_with_conn(conn, rows)
        return count
    finally:
        conn.close()


def _list_live_games_today(session: Optional[requests.Session] = None) -> List[int]:
    session = session or requests.Session()
    # Today's schedule only; can be extended to inch back/forward if desired

    today = datetime.now().strftime("%Y-%m-%d")
    games = fetch_schedule_for_date(today, session=session)
    rows = to_game_rows_from_schedule(games)
    # Ensure rows exist minimally (id and basic fields)
    conn = get_db_connection()
    try:
        upsert_games_with_conn(conn, rows)
    finally:
        conn.close()

    ids: List[int] = []
    for g in games:
        try:
            if str(g.get("gameState") or "").upper() == "LIVE":
                ids.append(int(g.get("id")))
        except Exception:
            continue
    return ids


def watch_live_games(poll_seconds: int = 5) -> None:
    session = requests.Session()
    i = 0
    while True:
        live_ids = _list_live_games_today(session=session)
        if not live_ids:
            print("No LIVE games found.")
        conn = get_db_connection()
        try:
            for game_id in live_ids:
                print(f"Watching game: {game_id}")
                landing = fetch_game_landing(game_id, session=session)
                box = fetch_game_boxscore(game_id, session=session)
                pbp = fetch_game_pbp(game_id, session=session)

                game_state, period, clock, home_score, away_score, home_sog, away_sog = derive_game_fields_from_gamecenter(landing, box)
                update_game_fields_with_conn(conn, game_id, game_state, period, clock, home_score, away_score, home_sog, away_sog)

                plays = pbp.get("plays") or []
                rows = [map_play(game_id, p) for p in plays]
                upsert_plays_with_conn(conn, rows)
        finally:
            conn.close()

        from time import sleep as _sleep
        if not live_ids:
            _sleep(60)
            continue
        _sleep(max(1, int(poll_seconds)))
        i += 1


