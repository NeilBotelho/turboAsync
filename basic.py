import asyncio
from threading import get_ident

import anyio
import httpx
import sniffio

from loop import CustomEventLoop, CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())



async def sleep_some():
    await asyncio.sleep(0.5)
    print("slept")


async def do_something(duration=12):
    await asyncio.gather(*[sleep_some() for _ in range(5)])
    # await asyncio.sleep(1)
    pass




async def try_req():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.google.com")


async def do():
    await asyncio.sleep(1)
    return 12



async def test_nested_async():
    loop = asyncio.get_running_loop()
    print("pre")
    await do()
    # coro=loop.getaddrinfo(
    #     host=b"google.com", port=80, family=0, type=1, proto=0, flags=0
    # )
    # print(await coro)
    print("done")
    return 12
# cor=test_nested_async()
# asyncio.run(cor)
if __name__ == "__main__":
    print("main", get_ident())
    # asyncio.run(fetch_google())
    asyncio.run(test_nested_async())

    print("done")
# asyncio.run(sleep_and_do())
