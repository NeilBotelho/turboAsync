from asyncio.tasks import Task
from asyncio import exceptions

_current_tasks = {}


def _enter_task(loop, task):
    # current_task = _current_tasks.get(loop)
    # if current_task is not None:
    #     raise RuntimeError(f"Cannot enter into task {task!r} while another "
    #                        f"task {current_task!r} is being executed.")
    _current_tasks[loop] = task


def _leave_task(loop, task):
    # current_task = _current_tasks.get(loop)
    # if current_task is not task:
    #     raise RuntimeError(f"Leaving task {task!r} does not match "
    #                        f"the current task {current_task!r}.")
    del _current_tasks[loop]


class CustomTask(Task):
    def __step(self, exc=None):
        if self.done():
            raise exceptions.InvalidStateError(
                f"_step(): already done: {self!r}, {exc!r}"
            )
        if self._must_cancel:
            if not isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = False
        self._fut_waiter = None

        _enter_task(self._loop, self)
        try:
            self.__step_run_and_handle_result(exc)
        finally:
            _leave_task(self._loop, self)
            self = None  # Needed to break cycles when an exception occurs.
