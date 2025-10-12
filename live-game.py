import argparse
import json
import os
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests
from dotenv import load_dotenv

try:
    import mysql.connector
except Exception as exc:  # pragma: no cover
    print("Missing mysql-connector-python. Please install requirements first.")
    raise


NHL_WEB_BASE = "https://api-web.nhle.com/v1"


# --------------------------------------------------
# Env and DB helpers (mirrors app.py patterns)
# --------------------------------------------------

load_dotenv()


def _get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def get_db_connection():  # type: ignore[no-untyped-def]
    return mysql.connector.connect(
        host=_get_env("DB_HOST", "127.0.0.1"),
        port=int(_get_env("DB_PORT", "3306")),
        user=_get_env("DB_USER", "root"),
        password=_get_env("DB_PASSWORD", ""),
        database=_get_env("DB_NAME"),
        autocommit=True,
    )


# --------------------------------------------------
# PBP fetch/load
# --------------------------------------------------


def fetch_game_play_by_play(game_id: int, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    session = session or requests.Session()
    url = f"{NHL_WEB_BASE}/gamecenter/{game_id}/play-by-play"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


def load_pbp_from_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# Update games from PBP-only fields
# --------------------------------------------------


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def derive_game_fields_from_pbp(pbp: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[str], int, int, int, int]:
    game_state = pbp.get("gameState")
    period = pbp.get("displayPeriod")

    # clock
    clock = pbp.get("clock").get("timeRemaining")

    # scores and SOG
    home = pbp.get("homeTeam") or {}
    away = pbp.get("awayTeam") or {}
    home_score = _safe_int(home.get("score")) if home.get("score") is not None else 0
    away_score = _safe_int(away.get("score")) if away.get("score") is not None else 0
    home_sog = _safe_int(home.get("sog")) if home.get("sog") is not None else 0
    away_sog = _safe_int(away.get("sog")) if away.get("sog") is not None else 0

    return (game_state, period, clock, home_score, away_score, home_sog, away_sog)


def update_games_from_pbp(game_id: int, pbp: Dict[str, Any]) -> None:
    game_state, period, clock, home_score, away_score, home_sog, away_sog = derive_game_fields_from_pbp(pbp)
    sql = (
        "UPDATE games SET gameState=%s, gamePeriod=%s, gameClock=%s, gameHomeScore=%s, gameAwayScore=%s, "
        "gameHomeSOG=%s, gameAwaySOG=%s WHERE gameId=%s"
    )
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            sql,
            (
                game_state,
                period,
                clock,
                home_score,
                away_score,
                home_sog,
                away_sog,
                game_id,
            ),
        )
        cur.close()
        
    finally:
        conn.close()


# --------------------------------------------------
# Plays upsert stub — mapping intentionally omitted
# --------------------------------------------------


RowMapper = Callable[[int, Dict[str, Any]], Optional[Tuple[Any, ...]]]

def map_play(game_id: int, play: dict):
        
    eventId = play.get("eventId")
    playId = game_id + eventId

    playIndex = play.get("sortOrder")
    playType = play.get("typeDescKey")
    playTime = play.get("timeInPeriod")
    playTimeReamaining = play.get("timeRemaining")

    playTeamId = None
    playXCoord = None
    playYCoord = None
    playPrimaryPlayerId = None
    playLosingPlayerId = None
    playSecondaryPlayerId = None
    playTertiaryPlayerId = None
    playZone = None
    playPeriod = None

    eventDetails = play.get("details")
    if isinstance(eventDetails, dict):
        playTeamId = eventDetails.get("eventOwnerTeamId") or None
        playXCoord = eventDetails.get("xCoord") or None
        playYCoord = eventDetails.get("yCoord") or None
        playPrimaryPlayerId = (eventDetails.get("playerId") or eventDetails.get("winningPlayerId")
            or eventDetails.get("hittingPlayerId") or eventDetails.get("shootingPlayerId")
            or eventDetails.get("blockingPlayerId") or eventDetails.get("committedByPlayerId")
            or eventDetails.get("scoringPlayerId") or None)
        playLosingPlayerId = (eventDetails.get("losingPlayerId") or eventDetails.get("hitteePlayerId")
            or eventDetails.get("shootingPlayerId") or eventDetails.get("goalieInNetId") or None)
        playSecondaryPlayerId = eventDetails.get("assist1PlayerId") or None
        playTertiaryPlayerId = eventDetails.get("assist2PlayerId") or None
        playZone = eventDetails.get("zoneCode") or None

    eventPeriodDescriptor = play.get("periodDescriptor")
    if isinstance(eventPeriodDescriptor, dict):
        playPeriod = eventPeriodDescriptor.get("number")

    return (
      playId, game_id, playIndex, playTeamId, playPrimaryPlayerId, playLosingPlayerId,
      playSecondaryPlayerId, playTertiaryPlayerId, playPeriod, playTime, playTimeReamaining,
      playType, playZone, playXCoord, playYCoord
    )


def upsert_plays_stub(game_id: int, pbp: Dict[str, Any]) -> int:
    plays = pbp.get("plays") or []
    if not plays:
        return 0

    rows: List[Tuple[Any, ...]] = []
    for play in plays:
        mapped = map_play(game_id, play)
        if mapped is not None:
            rows.append(mapped)
            print(f"Mapped play: {mapped}")

    if not rows:
        return 0

    sql = (
        "INSERT INTO plays (playId, playGameId, playIndex, playTeamId, playPrimaryPlayerId, playLosingPlayerId, "
        "playSecondaryPlayerId, playTertiaryPlayerId, playPeriod, playTime, playTimeReamaining,"
        "playType, playZone, playXCoord, playYCoord) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE playTeamId=VALUES(playTeamId), playPrimaryPlayerId=VALUES(playPrimaryPlayerId), "
        "playLosingPlayerId=VALUES(playLosingPlayerId), playSecondaryPlayerId=VALUES(playSecondaryPlayerId), "
        "playTertiaryPlayerId=VALUES(playTertiaryPlayerId), playPeriod=VALUES(playPeriod), playTime=VALUES(playTime), "
        "playTimeReamaining=VALUES(playTimeReamaining), playType=VALUES(playType), "
        "playZone=VALUES(playZone), playXCoord=VALUES(playXCoord), playYCoord=VALUES(playYCoord)"
    )

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        cur.close()
    finally:
        conn.close()
    return len(rows)


# --------------------------------------------------
# Runners (PBP-only)
# --------------------------------------------------


def update_once_from_web(game_id: int) -> int:
    session = requests.Session()
    pbp = fetch_game_play_by_play(game_id, session=session)
    update_games_from_pbp(game_id, pbp)
    return upsert_plays_stub(game_id, pbp)


def update_once_from_file(game_id: int, path: str) -> int:
    """
    Update from a json file saved locally for testing purposes.  
    """
    pbp = load_pbp_from_file(path)
    update_games_from_pbp(game_id, pbp)
    return upsert_plays_stub(game_id, pbp)


def watch_game(game_id: int, poll_seconds: int = 5) -> None:
    i = 0
    while True:
        print(f"{i} - Watching game: {game_id}")
        session = requests.Session()
        pbp = fetch_game_play_by_play(game_id, session=session)
        update_games_from_pbp(game_id, pbp)
        upsert_plays_stub(game_id, pbp)
        state = str(pbp.get("gameState") or "").lower()
        if state in {"final", "off", "gameover", "final_overtime", "final_shootout"}:
            break
        time.sleep(max(1, int(poll_seconds)))
        i += 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live NHL game updater (PBP-only shell)")
    parser.add_argument("game", type=int, help="Game ID (e.g., 2025020001)")
    parser.add_argument("--once", action="store_true", help="Run a single update instead of polling")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval in seconds")
    parser.add_argument("--from-file", type=str, default=None, help="Path to a local PBP JSON (e.g., services/db/test/game.json)")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    game_id = int(args.game)

    if args.from_file:
        count = update_once_from_file(game_id, args.from_file)
        print(f"Updated game {game_id} from file; upserted {count} plays.")
        return 0

    if args.once:
        count = update_once_from_web(game_id)
        print(f"Updated game {game_id}; upserted {count} plays.")
        return 0

    watch_game(game_id, poll_seconds=int(args.poll_seconds))
    print(f"Finished watching game {game_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


