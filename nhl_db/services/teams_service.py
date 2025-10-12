from typing import Any, Dict, List

from ..clients.records_client import fetch_franchises
from ..mappers.teams import to_team_rows
from ..repositories.teams_repo import upsert_teams


def sync_teams_records() -> int:
    franchises: List[Dict[str, Any]] = fetch_franchises()
    rows = to_team_rows(franchises)
    upsert_teams(rows)
    return len(rows)


