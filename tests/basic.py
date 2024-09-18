import asyncio


from turboasync.loop import CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())


async def gather_sleep():
    await asyncio.gather(*[asyncio.sleep(0.5) for _ in range(3)])


async def test_nested_async():
    print("Start of async function")
    await gather_sleep()
    print("call_later works correctly")
    return 12


if __name__ == "__main__":
    asyncio.run(test_nested_async())
    print("async function exits correctly")
