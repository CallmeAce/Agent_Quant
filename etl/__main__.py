"""
Package entrypoint so `python -m etl` runs the scheduler.
"""

from __future__ import annotations

import asyncio

from etl.scheduler import main

if __name__ == "__main__":
    asyncio.run(main())
