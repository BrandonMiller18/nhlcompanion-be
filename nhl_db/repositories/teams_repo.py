from typing import Any, List, Tuple

from ..db import get_db_connection


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
        cur.executemany(sql, rows)
        cur.close()
    finally:
        conn.close()


