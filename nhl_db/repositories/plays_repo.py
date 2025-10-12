from typing import Any, Dict, List, Tuple

from ..db import get_db_connection


def upsert_plays_from_pbp(game_id: int, pbp: Dict[str, Any], rows: List[Tuple[Any, ...]]) -> int:
    if not rows:
        return 0

    sql = (
        "INSERT INTO plays (playId, playGameId, playIndex, playTeamId, playPrimaryPlayerId, playLosingPlayerId, "
        "playSecondaryPlayerId, playTertiaryPlayerId, playPeriod, playTime, playTimeReamaining, "
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


def upsert_plays_with_conn(conn, rows: List[Tuple[Any, ...]]) -> int:  # type: ignore[no-untyped-def]
    if not rows:
        return 0

    sql = (
        "INSERT INTO plays (playId, playGameId, playIndex, playTeamId, playPrimaryPlayerId, playLosingPlayerId, "
        "playSecondaryPlayerId, playTertiaryPlayerId, playPeriod, playTime, playTimeReamaining, "
        "playType, playZone, playXCoord, playYCoord) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE playTeamId=VALUES(playTeamId), playPrimaryPlayerId=VALUES(playPrimaryPlayerId), "
        "playLosingPlayerId=VALUES(playLosingPlayerId), playSecondaryPlayerId=VALUES(playSecondaryPlayerId), "
        "playTertiaryPlayerId=VALUES(playTertiaryPlayerId), playPeriod=VALUES(playPeriod), playTime=VALUES(playTime), "
        "playTimeReamaining=VALUES(playTimeReamaining), playType=VALUES(playType), "
        "playZone=VALUES(playZone), playXCoord=VALUES(playXCoord), playYCoord=VALUES(playYCoord)"
    )

    cur = conn.cursor()
    try:
        cur.executemany(sql, rows)
    finally:
        cur.close()
    return len(rows)


