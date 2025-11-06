from typing import Any, List, Tuple
import logging

from ..db import get_db_connection

logger = logging.getLogger(__name__)


def upsert_players(rows: List[Tuple[Any, ...]]) -> None:
    if not rows:
        return
    sql = (
        "INSERT INTO players (playerId, playerTeamId, playerFirstName, playerLastName, playerNumber, "
        "playerPosition, playerHeadshotUrl, playerHomeCity, playerHomeCountry) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE playerTeamId=VALUES(playerTeamId), playerFirstName=VALUES(playerFirstName), "
        "playerLastName=VALUES(playerLastName), playerNumber=VALUES(playerNumber), playerPosition=VALUES(playerPosition), "
        "playerHeadshotUrl=VALUES(playerHeadshotUrl), playerHomeCity=VALUES(playerHomeCity), playerHomeCountry=VALUES(playerHomeCountry)"
    )
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.executemany(sql, rows)
        except Exception as e:
            logger.error(f"Database error upserting {len(rows)} players: {e}", exc_info=True)
            raise
        finally:
            cur.close()
    finally:
        conn.close()


