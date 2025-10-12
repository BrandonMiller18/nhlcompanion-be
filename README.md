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
pip install -r services/db/requirements.txt
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
Get-Content services\db\test\schema.sql | mysql -h $env:DB_HOST -P $env:DB_PORT -u $env:DB_USER -p$env:DB_PASSWORD $env:DB_NAME
```

### Recommended usage flow
Run commands from the repository root so `.env` is picked up.

1) Import teams (Records API franchises) – required before players/games
```powershell
python services/db/app.py sync-teams-records
```

2) Import players via roster for a season (NHL Web API)
```powershell
# Season format: YYYYYYYY (e.g., 20252026). Limit to triCodes if desired.
python services/db/app.py sync-players-roster 20252026 --teams STL,VGK,SEA
# For all active teams, omit --teams
```

3) Import schedule by date range (inclusive)
```powershell
python services/db/app.py sync-schedule-dates 2025-09-20 2025-10-15
```

4) Update a single live game (by gameId) on demand
```powershell
python services/db/app.py update-live 2025020001
```

5) Continuously watch all LIVE games and update DB
```powershell
python services/db/app.py watch-live --poll-seconds 5
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
  - API: For each active team, GET `NHL_WEB_BASE/roster/{triCode}/{season}`; merge `forwards` + `defensemen` + `goalies`
  - Transform: Map ids, first/last names, number, position, headshot, origin; include `playerTeamId`
  - DB: Upsert into `players` with FK to `teams(teamId)`

- Schedule (sync-schedule-dates)
  - API: For each date in range, GET `NHL_WEB_BASE/schedule/{YYYY-MM-DD}`, flatten `gameWeek[].games[]`
  - Transform: Map game id, season, type, UTC start, venue, home/away team ids, state, and any scores available
  - DB: Upsert into `games` (includes `gameState`, scores, venue, and team FKs)

- Live single game (update-live)
  - API: GET landing, boxscore, pbp for `gameId`
  - Transform: Derive `gameState`, `gamePeriod`, `gameClock`, `gameHomeScore`, `gameAwayScore`, `gameHomeSOG`, `gameAwaySOG`; map pbp events to `plays`
  - DB: Update `games` fields; upsert `plays` events keyed by `(playId, playIndex)`

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

### Troubleshooting
- Ensure dependencies are installed: `pip install -r services/db/requirements.txt`
- Verify `.env` values match your MySQL instance; `DB_NAME` is required.
- If the `mysql` CLI isn’t on PATH, open `services/db/test/schema.sql` in MySQL Workbench and run it.
- Corporate proxies/firewalls can block requests to `records.nhl.com` and `api-web.nhle.com`.


