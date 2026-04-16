"""CLI entry point for JiuZhang."""

import sys
from jiuzhang.cli_app import main as cli_main


def main():
    """Main entry point for the jiuzhang command."""
    if len(sys.argv) > 1 and sys.argv[1] in (
        "cli",
        "learn",
        "exercise",
        "visualize",
        "config",
    ):
        cli_main(sys.argv[1:])
    else:
        try:
            from jiuzhang.app import run_web

            run_web()
        except ImportError:
            cli_main(["learn", "数的概念"])


if __name__ == "__main__":
    main()
