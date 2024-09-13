import asyncio
import socket


class HttpParserError(Exception):
    pass


class HTTPparser:
    def __init__(self):
        self.request = {}

    def parse_request(self, http_data):
        try:
            request, headers_body = http_data.split(b'\r\n', 1)
            self.request["method"], self.request["path"], type_version = request.split(b' ')
            *headers, self.request["body"] = headers_body.split(b'\r\n')
            self.request["type"], self.request["http_version"] = type_version.split(b'/')

            formatted_headers = []
            for header in headers:
                try:
                    key, val = header.split(b':', maxsplit=1)
                    val = val.strip()
                    formatted_headers.append((key, val))
                except Exception as e:
                    pass
            self.request["headers"] = formatted_headers

        except Exception as e:
            raise HttpParserError()

    def serialize_http_response(self, asgi_responses):
        http_response = b""
        headers = {}

        for response in asgi_responses:
            response_type = response.get("type")

            if response_type == "http.response.start":
                status_code = response.get("status", 200)
                http_response += f"HTTP/1.1 {status_code} OK\r\n".encode()

                for header in response.get("headers", []):
                    key, value = header
                    headers[key] = value

            elif response_type == "http.response.body":
                http_response += b"\r\n".join(
                    [f"{key.decode()}: {value.decode()}".encode() for key, value in headers.items()])
                http_response += b"\r\n\r\n" + response.get("body", b"")

        return http_response

class ASGIspec:
    def __init__(self, http_parse: HTTPparser):
        self.scope: dict = {
            'asgi': {
                'version': '3.0',
                'spec_version': '2.0'
            },
            'method': http_parse.request['method'].decode(),
            'type': http_parse.request['type'].decode().lower(),
            'http_version': http_parse.request['http_version'].decode(),
            'path': http_parse.request['path'].decode(),
            'headers': http_parse.request['headers'],
            'query_string': b'',
        }
        self.http_parse = http_parse.request
        self.response = []
        self.response_event = asyncio.Event()

    async def run(self, app):
        await app(self.scope, self.receive, self.send)

    async def send(self, message):
        self.response.append(message)
        if message.get('type') == "http.response.body":
            self.response_event.set()

    async def receive(self):
        message = {
            "type": "http.request",
            "body": self.http_parse['body'],
            "more_body": False,
        }
        return message


class ConnectionHandler:
    def __init__(self, app, connection, loop):
        self.app = app
        self.connection = connection
        self.loop = loop
        self.parser = HTTPparser()

    async def handle_connection(self):
        try:
            data = await self.loop.sock_recv(self.connection, 1024)
            self.parser.parse_request(data)
            asgi_spec = ASGIspec(self.parser)
            asyncio.create_task(asgi_spec.run(self.app))
            await asgi_spec.response_event.wait()
            http_response = self.parser.serialize_http_response(asgi_spec.response)
            await self.loop.sock_sendall(self.connection, http_response)

        except HttpParserError as e:
            print("Http parser exception...", e)
        except Exception as e:
            print(e)
        finally:
            self.connection.close()


class Server:
    def __init__(self, app, host, port):
        self.app = app
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind((self.host, self.port))

    async def listen_for_connections(self, loop):
        self.server_socket.listen()
        print(f"Listening on {self.host, self.port}")
        while True:
            connection, address = await loop.sock_accept(self.server_socket)
            print(f"{address} connected")
            connection_handler = ConnectionHandler(self.app, connection, loop)
            asyncio.create_task(connection_handler.handle_connection())

    async def start(self):
        loop = asyncio.get_event_loop()
        await self.listen_for_connections(loop)
