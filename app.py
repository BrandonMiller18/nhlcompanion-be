import argparse
import sys
from typing import List, Optional

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NHL DB Sync - stepwise")
    sub = parser.add_subparsers(dest="command", required=True)

    # Defer command registration to modular command modules
    try:
        from nhl_db.commands.teams import register as register_teams
        register_teams(sub)
    except Exception:
        pass

    try:
        from nhl_db.commands.players import register as register_players
        register_players(sub)
    except Exception:
        pass

    try:
        from nhl_db.commands.schedule import register as register_schedule
        register_schedule(sub)
    except Exception:
        pass

    try:
        from nhl_db.commands.live import register as register_live
        register_live(sub)
    except Exception:
        pass

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())


