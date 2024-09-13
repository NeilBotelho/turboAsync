import asyncio
import time
import socket
from threading import get_ident
import httpx
import sniffio
from loop import CustomEventLoop, CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())

sniffio.current_async_library_cvar.set("asyncio")

host="142.250.199.174"
port=443 
address=None

async def httpx_request():
    async with httpx.AsyncClient() as client:
            response = await client.get('https://www.google.com')
            print(response)
            return response.text

# async def request_test():
#     loop=asyncio.get_running_loop() protocol=lambda: asyncio.StreamReaderProtocol(asyncio.StreamReader(), loop=loop)
#     try :
#         print("####RESULT",await loop.create_connection(protocol,host,port,local_addr=address))
#     except Exception as e:
#         print(e)

def do_sleep(fut):
    print("done",fut)
    return
async def fut_test():
    loop=asyncio.get_running_loop()
    fut=loop.create_future()
    # asyncio.events.Handle(do_sleep)
    fut.add_done_callback(do_sleep)
    fut.set_result(5)
async def sock_test():
    loop=asyncio.get_running_loop()
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    sock.setblocking(False)
    print('a',await loop.sock_connect(sock, (host,port)))
    return 12
    # loop=asyncio.get_running_loop()
    # loop.sock_connect()

if __name__ == "__main__":
    # asyncio.run(request_test())
    print(asyncio.run(httpx_request()))
    asyncio.run(sock_test())
