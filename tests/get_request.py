import asyncio
import httpx
import sniffio
from turboasync.loop import CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())

sniffio.current_async_library_cvar.set("asyncio")

host = "142.250.199.174"
port = 443
address = None


async def httpx_request():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.google.com")
        return response.text


if __name__ == "__main__":
    print(asyncio.run(httpx_request()))
