from typing import Any, List, Tuple
import logging

from ..db import get_db_connection

logger = logging.getLogger(__name__)


def upsert_teams(rows: List[Tuple[Any, ...]]) -> None:
    if not rows:
        return
    sql = (
        "INSERT INTO teams (teamId, teamName, teamCity, teamAbbrev, teamIsActive, teamLogoUrl) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE teamName=VALUES(teamName), teamCity=VALUES(teamCity), teamAbbrev=VALUES(teamAbbrev), "
        "teamIsActive=VALUES(teamIsActive), teamLogoUrl=VALUES(teamLogoUrl)"
    )
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.executemany(sql, rows)
        except Exception as e:
            logger.error(f"Database error upserting {len(rows)} teams: {e}", exc_info=True)
            raise
        finally:
            cur.close()
    finally:
        conn.close()


