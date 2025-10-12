from typing import Any, Dict, List, Optional, Tuple


def map_play(game_id: int, p: Dict[str, Any]) -> Tuple[Any, ...]:
    play_id = game_id + p.get("eventId", 0)
    idx = p.get("sortOrder", 0)

    period = None
    time_str = None
    time_remaining = None
    seconds_elapsed = None
    pd = p.get("periodDescriptor") or {}
    if isinstance(pd, dict):
        period = pd.get("number")
        time_remaining = pd.get("timeRemaining")
        time_str = pd.get("timeElapsed") or time_remaining

    team_id = None
    if isinstance(p.get("team"), dict):
        team_id = p["team"].get("id")
    if team_id is None and isinstance(p.get("details"), dict):
        team_id = p["details"].get("eventOwnerTeamId")
    try:
        team_id = int(team_id) if team_id is not None else None
    except Exception:
        team_id = None

    details = p.get("details") or {}
    primary_id = details.get("shootingPlayerId") or details.get("scoringPlayerId") or details.get("hittingPlayerId") or details.get("winningPlayerId")
    losing_id = details.get("losingPlayerId")
    sec_ids = details.get("assistingPlayerIds") or []
    secondary_id = sec_ids[0] if len(sec_ids) > 0 else None
    tertiary_id = sec_ids[1] if len(sec_ids) > 1 else None

    x = details.get("xCoord")
    y = details.get("yCoord")
    zone = details.get("zoneCode")
    ptype = p.get("typeDescKey") or (p.get("type") or {}).get("value")

    return (
        play_id,
        game_id,
        int(idx),
        team_id,
        primary_id,
        losing_id,
        secondary_id,
        tertiary_id,
        period,
        time_str,
        time_remaining,
        ptype,
        zone,
        x,
        y,
    )


