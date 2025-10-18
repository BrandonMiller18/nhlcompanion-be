## NHL Companion – Database Sync and Live Updater

Utilities to populate and keep a local MySQL database in sync with NHL data. It pulls from two public APIs:

- Records API (historical teams): `https://records.nhl.com/site/api`
- NHL Web API (rosters, schedules, live game data): `https://api-web.nhle.com/v1`

This README covers installation, environment/database setup, recommended usage/order of operations, command reference, and service workflows (API calls ↔ database writes).

### Prerequisites
- Python 3.10+
- MySQL 8.x (or compatible)
- Windows PowerShell examples below; adapt to your shell as needed

### Install
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configure database
1) Create a database (example name: nhl):
```sql
CREATE DATABASE nhl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2) Provide environment variables (either in a `.env` at the repository root or exported in your shell):
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=nhl
```

3) Load schema:
```powershell
# If your password is blank, drop -p$env:DB_PASSWORD
Get-Content test\schema.sql | mysql -h $env:DB_HOST -P $env:DB_PORT -u $env:DB_USER -p$env:DB_PASSWORD $env:DB_NAME
```

### Recommended usage flow
Run commands from the `/db` directory (the repository root) so `.env` is picked up.

1) Import teams (Records API franchises) – required before players/games
```powershell
python app.py sync-teams-records
```

2) Import players via roster for a season (NHL Web API)
```powershell
# Season format: YYYYYYYY (e.g., 20252026). Limit to triCodes if desired.
python app.py sync-players-roster 20252026 --teams STL,VGK,SEA
# For all active teams, omit --teams
```

3) Import schedule by date range (inclusive)
```powershell
python app.py sync-schedule-dates 2025-09-20 2025-10-15
```

4) Update a single live game (by gameId) on demand
```powershell
python app.py update-live 2025020001
```

5) Continuously watch all LIVE games and update DB
```powershell
python app.py watch-live --poll-seconds 5
```

### Command reference
- sync-teams-records
  - Source: Records API franchises
  - Effect: Upserts rows into `teams`

- sync-players-roster <season> [--teams TRI,TRI]
  - Source: NHL Web API roster per team and season
  - Effect: For each active team (optionally filtered), upserts `players`
  - Season format: YYYYMMDD (e.g., 20252026)

- sync-schedule-dates <start YYYY-MM-DD> <end YYYY-MM-DD>
  - Source: NHL Web API daily schedule per date
  - Effect: Flattens `gameWeek[].games[]`, upserts `games`

- update-live <gameId>
  - Source: NHL Web API gamecenter (landing, boxscore, play-by-play)
  - Effect: Updates `games` state/period/clock/scores/SOG and upserts `plays`

- watch-live [--poll-seconds N]
  - Source: For today, lists LIVE games from schedule; then polls landing/boxscore/pbp per game
  - Effect: Continuously updates `games` and `plays` for all LIVE games

### Service workflows

- Teams (sync-teams-records)
  - API: GET `RECORDS_BASE/franchise?include=...`
  - Transform: Choose dark logo with highest `startSeason`; map names and flags
  - DB: Upsert into `teams(teamId, teamName, teamCity, teamAbbrev, teamIsActive, teamLogoUrl)`

- Players (sync-players-roster)
  - API (dual-source):
    1. Primary: GET `NHL_WEB_BASE/roster/{triCode}/{season}` – merge `forwards` + `defensemen` + `goalies`
    2. Secondary: GET `RECORDS_BASE/player/byTeam/{teamId}` – fill in players missing from NHL Web roster
  - Merge strategy: Dedupe by player ID; prefer NHL Web data entirely when present; Records API fills gaps (e.g., injured reserve, historical rosters)
  - Transform: Map ids, first/last names, sweater number, position, headshot (NHL Web only), birth city/country; respect per-player `currentTeamId` from Records if available
  - DB: Upsert into `players` with FK to `teams(teamId)`

- Schedule (sync-schedule-dates)
  - API: For each date in range, GET `NHL_WEB_BASE/schedule/{YYYY-MM-DD}`, flatten `gameWeek[].games[]`
  - Transform: Map game id, season, type, UTC start, venue, home/away team ids, state, and any scores available
  - DB: Upsert into `games` (includes `gameState`, scores, venue, and team FKs)

- Live single game (update-live)
  - API: GET landing, boxscore, pbp for `gameId`
  - Transform: Derive `gameState`, `gamePeriod`, `gameClock`, `gameHomeScore`, `gameAwayScore`, `gameHomeSOG`, `gameAwaySOG`; map pbp events to `plays`
  - playId generation: Concatenate `gameId` + `eventId` as strings, then convert to integer (e.g., game 2025020076 event 54 → playId 20250200760054). Stored as `BIGINT` to handle values exceeding standard `INT` range
  - DB: Update `games` fields; upsert `plays` events keyed by unique `playId` (primary key)

- Live watcher (watch-live)
  - API: For today, fetch schedule, upsert any games; poll only games with `gameState == LIVE`
  - Transform/DB: Same as single game, repeated every `--poll-seconds`

### Verification snippets
```sql
-- Teams
SELECT COUNT(*) FROM teams;
SELECT teamId, teamName, teamCity, teamAbbrev, teamIsActive, teamLogoUrl FROM teams LIMIT 10;

-- Players for a team
SELECT COUNT(*) FROM players WHERE playerTeamId = (SELECT teamId FROM teams WHERE teamAbbrev='STL');

-- Games in a window
SELECT COUNT(*) FROM games WHERE gameDateTimeUtc BETWEEN '2025-09-20' AND '2025-10-16';
```

### Notes and recommendations
- Run `sync-teams-records` first; many other steps rely on team IDs.
- Load players for the relevant season before ingesting live plays for that season for richer joins.
- Import a date window of the schedule before starting live updates to pre-seed `games` rows.
- Player roster sync uses a dual-source strategy: NHL Web API provides current active rosters with headshots; Records API supplements with players not in the active roster (injured reserve, recently traded, or historical players). This ensures comprehensive coverage.
- Play IDs are generated by concatenating `gameId` + `eventId` to ensure global uniqueness across all games. The `playId` column uses `BIGINT` because concatenated values can exceed 2.1 billion (e.g., game 2025020076 with eventId 54 produces playId 20250200760054).

### Troubleshooting
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Verify `.env` values match your MySQL instance; `DB_NAME` is required.
- If the `mysql` CLI isn't on PATH, open `test/schema.sql` in MySQL Workbench and run it.
- Corporate proxies/firewalls can block requests to `records.nhl.com` and `api-web.nhle.com`.


