import sys
import asyncio

import handler

if __name__ == "__main__":
    sys.exit(asyncio.run(handler.run()))