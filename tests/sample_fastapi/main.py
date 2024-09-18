import asyncio
import importlib

from turboasync.loop import CustomPolicy

asyncio.set_event_loop_policy(CustomPolicy())


class NoAppFoundError(Exception):
    pass


def get_from_str(input_str):
    module_str, attrs_str = input_str.split(":")
    try:
        module = importlib.import_module(module_str)
        app = getattr(module, attrs_str)
        return app
    except ModuleNotFoundError:
        raise NoAppFoundError()


def main():
    pass
    # app = get_from_str(sys.argv[1])
    # server = Server(app, '127.0.0.1', 8000)
    # print(app)
    # asyncio.run(server.start())


if __name__ == "__main__":
    main()
