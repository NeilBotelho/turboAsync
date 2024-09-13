import asyncio
import tasks
import sys
import threading
import time
from asyncio.events import Handle, _get_running_loop, _set_running_loop
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from queue import Queue

import sniffio

from compat import ScheduleThread, SelectorThread



class CustomPolicy(asyncio.unix_events._UnixDefaultEventLoopPolicy):
    def __init__(self, loop=None):
        self.loop = loop
        super().__init__()

    def _loop_factory(self):
        # Also add a condition for events.get_running loop
        if self.loop is None:
            return CustomEventLoop()
        return self.loop




class CustomEventLoop(asyncio.SelectorEventLoop):
    def __init__(self, selector=None, workers=3):
        super().__init__(selector)
        self.print_lock = threading.RLock()
        # initialize workers here
        self.main_thread = threading.get_ident()
        self.readyq = Queue()
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.nworkers = workers
        self._scheduled = Queue()
        self.schedule_thread = ScheduleThread(
            ready_queue=self.readyq, scheduled_queue=self._scheduled
        )
        self.schedule_thread.run_forever_in_thread()
        self.selector_thread=SelectorThread(ready_queue=self.readyq,selector=self._selector,selector_lock=threading.RLock(),loop=self)
        self.selector_thread.run_forever_in_thread()
        sniffio.current_async_library_cvar.set("asyncio")

    def print(self, *args):
        with self.print_lock:
            print(*args)

    def _check_running(self):
        pass

    def _check_thread(self):
        pass

    def stop(self):
        self._stopping = True
        # self.readyq.put(StopException())

    def close(self):
        self._closed = True
        with self.readyq.mutex:
            self.readyq.queue.clear()
        self.schedule_thread.close()

    @classmethod
    def make_worker_func(cls, loop):
        asyncio.set_event_loop(loop)
        sniffio.current_async_library_cvar.set("asyncio")
        asyncio.events._set_running_loop(loop)
        loop._run_once()

    def running_on_main_thread(self):
        return threading.get_ident() == self.main_thread

    def run_forever(self):
        """Run until stop() is called."""
        self._check_closed()
        self._set_coroutine_origin_tracking(self._debug)
        old_agen_hooks = sys.get_asyncgen_hooks()
        try:
            sys.set_asyncgen_hooks(
                firstiter=self._asyncgen_firstiter_hook,
                finalizer=self._asyncgen_finalizer_hook,
            )
            _set_running_loop(self)
            _get_running_loop()
            while not self._stopping:
                if self.readyq.qsize() == 0:
                    if (
                        self._scheduled.qsize() == 0
                        and self.schedule_thread.sorted_scheduled.is_empty()
                        and self.readyq.qsize() == 0
                    ):
                        print("breaking")
                        pass
                        # time.sleep(0.5)
                        # break

                num_jobs = self.readyq.qsize()
                num_workers = num_jobs - 1 if num_jobs > 1 else 1
                # num_workers=min(self.nworkers,num_jobs)
                # print(self.readyq.readyqqueue)
                self.selector_thread.run_once()
                # self._run_once()
                [
                    x
                    for x in self.pool.map(
                        CustomEventLoop.make_worker_func,
                        [self for _ in range(num_workers)],
                    )
                ]

        finally:
            self._stopping = False
            self._thread_id = None
            _set_running_loop(None)
            self._set_coroutine_origin_tracking(False)
            sys.set_asyncgen_hooks(*old_agen_hooks)

    async def shutdown_asyncgens(self):
        pass

    def _run_once(self):
        """Run one full iteration of the event loop.

        This calls all currently ready callbacks, polls for I/O,
        schedules the resulting callbacks, and finally schedules
        'call_later' callbacks.
        """
        handle = self.readyq.get(timeout=None, block=True)
        print("RUNNING handle",handle)
        if not handle._cancelled:
            handle._run()
        handle = None
    
    def create_task(self, coro, *, name=None, context=None):
        """Schedule a coroutine object.

        Return a task object.
        """
        self._check_closed()
        if self._task_factory is None:
            task = tasks.Task(coro, loop=self, name=name, context=context)
            if task._source_traceback:
                del task._source_traceback[-1]
        else:
            if context is None:
                # Use legacy API if context is not needed
                task = self._task_factory(self, coro)
            else:
                task = self._task_factory(self, coro, context=context)

            task.set_name(name)

        return task


    def _add_callback(self, handle):
        """Add a Handle to _ready."""
        if not handle._cancelled:
            self.readyq.put(handle)

    def create_task(self, coro, *, name=None, context=None):
        """Schedule a coroutine object.

        Return a task object.
        """
        self._check_closed()
        task = tasks.Task(coro, loop=self, name=name, context=context)
        if task._source_traceback:
            del task._source_traceback[-1]

        return task
    def _call_soon(self, callback, args, context):
        handle = Handle(callback, args, self, context)
        if handle._source_traceback:
            del handle._source_traceback[-1]
        self.readyq.put(handle)
        return handle

    def call_at(self, when, callback, *args, context=None):
        if when is None:
            raise TypeError("when cannot be None")
        self._check_closed()
        timer = asyncio.events.TimerHandle(when, callback, args, self, context)
        if timer._source_traceback:
            del timer._source_traceback[-1]
        self._scheduled.put(timer, block=True)
        timer._scheduled = True
        return timer

