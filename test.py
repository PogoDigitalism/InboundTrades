from src.utils import SyncInAsync
import asyncio
import time

def test():
    for i in range(10):
        print(i)
        time.sleep(1)

async def main():
    sia = SyncInAsync()

    await sia.Call(test)

    print("FREE")

asyncio.run(main())