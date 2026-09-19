#!/usr/bin/env python3
"""Pokemon GO roster and bag optimizer.

    source .venv/bin/activate
    python rank.py --help

Commands live in pogo/cli.py.
"""

import sys

from pogo.cli import main

if __name__ == "__main__":
    sys.exit(main())
