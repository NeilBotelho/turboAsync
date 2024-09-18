import asyncio
import socket
import sniffio
from turboasync.loop import CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())

sniffio.current_async_library_cvar.set("asyncio")

host = "127.0.0.1"
port = 8000
address = None


async def sock_test():
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    sock.bind((host, port))
    sock.listen()
    print(await loop.sock_accept(sock))
    print("accepted connection")


if __name__ == "__main__":
    asyncio.run(sock_test())
    # use the command:
    # telnet 127.0.0.1 8000
    # to verify
