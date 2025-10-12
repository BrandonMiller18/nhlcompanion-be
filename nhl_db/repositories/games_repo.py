from typing import Any, List, Optional, Tuple

from ..db import get_db_connection


def upsert_games(rows: List[Tuple[Any, ...]]) -> None:
    if not rows:
        return
    sql = (
        "INSERT INTO games (gameId, gameSeason, gameType, gameDateTimeUtc, gameVenue, gameHomeTeamId, gameAwayTeamId, "
        "gameState, gameHomeScore, gameAwayScore) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE gameSeason=VALUES(gameSeason), gameType=VALUES(gameType), gameDateTimeUtc=VALUES(gameDateTimeUtc), "
        "gameVenue=VALUES(gameVenue), gameHomeTeamId=VALUES(gameHomeTeamId), gameAwayTeamId=VALUES(gameAwayTeamId), "
        "gameState=VALUES(gameState), gameHomeScore=VALUES(gameHomeScore), "
        "gameAwayScore=VALUES(gameAwayScore)"
    )
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        cur.close()
    finally:
        conn.close()


def update_game_fields(game_id: int, game_state: Optional[str], period: Optional[int], clock: Optional[str], home_score: int, away_score: int, home_sog: int, away_sog: int) -> None:
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


def upsert_games_with_conn(conn, rows: List[Tuple[Any, ...]]) -> None:  # type: ignore[no-untyped-def]
    if not rows:
        return
    sql = (
        "INSERT INTO games (gameId, gameSeason, gameType, gameDateTimeUtc, gameVenue, gameHomeTeamId, gameAwayTeamId, "
        "gameState, gameHomeScore, gameAwayScore) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE gameSeason=VALUES(gameSeason), gameType=VALUES(gameType), gameDateTimeUtc=VALUES(gameDateTimeUtc), "
        "gameVenue=VALUES(gameVenue), gameHomeTeamId=VALUES(gameHomeTeamId), gameAwayTeamId=VALUES(gameAwayTeamId), "
        "gameState=VALUES(gameState), gameHomeScore=VALUES(gameHomeScore), gameAwayScore=VALUES(gameAwayScore)"
    )
    cur = conn.cursor()
    try:
        cur.executemany(sql, rows)
    finally:
        cur.close()


def update_game_fields_with_conn(conn, game_id: int, game_state: Optional[str], period: Optional[int], clock: Optional[str], home_score: int, away_score: int, home_sog: int, away_sog: int) -> None:  # type: ignore[no-untyped-def]
    sql = (
        "UPDATE games SET gameState=%s, gamePeriod=%s, gameClock=%s, gameHomeScore=%s, gameAwayScore=%s, "
        "gameHomeSOG=%s, gameAwaySOG=%s WHERE gameId=%s"
    )
    cur = conn.cursor()
    try:
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
    finally:
        cur.close()


