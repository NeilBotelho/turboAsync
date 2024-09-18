import heapq
import asyncio
from threading import RLock
from selectors import BaseSelector
import threading
import time
from queue import Empty, Queue
from typing import Optional


class SimplePriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, item):
        # Priority queue items are tuples (priority, item)
        heapq.heappush(self.heap, item)

    def pop(self):
        if not self.heap:
            raise IndexError("pop from an empty priority queue")
        # Pop the smallest item (which has the lowest priority)
        return heapq.heappop(self.heap)

    def peek(self):
        if not self.heap:
            raise IndexError("peek from an empty priority queue")
        # Peek at the smallest item (which has the lowest priority)
        return self.heap[0]

    def is_empty(self):
        return len(self.heap) == 0


class ScheduleThread:
    def __init__(self, ready_queue: Queue, scheduled_queue: Optional[Queue] = None):
        if scheduled_queue is None:
            scheduled_queue = Queue()
        self.scheduled = scheduled_queue
        self.sorted_scheduled = SimplePriorityQueue()
        self.ready = ready_queue
        self._clock_resolution = time.get_clock_info("monotonic").resolution
        self.handle = None

    def time(self):
        return time.monotonic()

    def wait_for_new_scheduled_items(self, timeout=None):
        try:
            event = self.scheduled.get(block=True, timeout=timeout)
        except Empty:
            return
        self.sorted_scheduled.push(item=event)
        return

    def dispatch(self):
        curr_time = self.time() + self._clock_resolution
        while not self.sorted_scheduled.is_empty():
            handle = self.sorted_scheduled.peek()
            if handle._when >= curr_time:
                break
            handle = self.sorted_scheduled.pop()
            handle._scheduled = False
            self.ready.put(handle)

    def read_and_dispatch(self):
        if self.sorted_scheduled.is_empty():
            timeout = None
        else:
            timeout = max(0, self.time() - self.sorted_scheduled.peek()._when)
        self.wait_for_new_scheduled_items(timeout=timeout)
        self.dispatch()

    def close(self):
        with self.scheduled.mutex:
            self.scheduled.queue.clear()

    def run_forever_in_thread(self):
        self.handle = threading.Thread(target=self.run_forever)
        self.handle.daemon = True
        self.handle.start()

    def run_forever(self):
        while True:
            self.read_and_dispatch()


class SelectorThread:
    def __init__(
        self,
        ready_queue: Queue,
        selector: BaseSelector,
        selector_lock: RLock,
        loop: asyncio.BaseEventLoop,
    ):
        self.ready = ready_queue
        self.selector = selector
        self.lock = selector_lock
        self.loop = loop

    def run_once(self):
        event_list = self.selector.select(timeout=0)
        with self.lock:
            self.loop._process_events(event_list)

    def run_forever(self):
        while True:
            event_list = self.selector.select(timeout=None)
            with self.lock:
                self.loop._process_events(event_list)
            event_list = None

    def run_forever_in_thread(self):
        self.handle = threading.Thread(target=self.run_forever)
        self.handle.daemon = True
        self.handle.start()
