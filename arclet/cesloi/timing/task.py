import asyncio
import traceback
from datetime import datetime
from typing import Callable
from .timers import Timer
from .event import ScheduleTaskEvent
from .schedule import EventSystem
from ...letoderea import Subscriber
from ...letoderea.handler import await_exec_target

class TimingTask:
    callable_target: Callable
    task: asyncio.Task
    timer: Timer
    event_system: EventSystem
    is_disposable: bool = False
    is_stop: bool = False
    is_start: bool = False
    interval_offset: float = 0

    def __init__(
            self,
            callable_target: Callable,
            timer: Timer,
            event_system: EventSystem,
            is_disposable: bool = False,
    ) -> None:
        self.callable_target = callable_target
        self.timer = timer
        self.event_system = event_system
        self.is_disposable = is_disposable

    def set_task(self):
        if not self.is_start:
            self.task = self.event_system.loop.create_task(self.run_task())
        else:
            raise RuntimeError("the scheduler task has been started!")

    def interval_generator(self):
        for next_execute_time in self.timer.get_delta():
            if self.is_stop:
                return
            now = datetime.now()
            if next_execute_time >= now:
                yield (next_execute_time - now).total_seconds() - self.interval_offset

    def coroutine_generator(self):
        for sleep_interval in self.interval_generator():
            yield asyncio.sleep(sleep_interval), True
            yield await_exec_target(
                Subscriber.set()(self.callable_target), ScheduleTaskEvent.get_params
            ), False

    async def run_task(self) -> None:
        for coro, waiting in self.coroutine_generator():
            if waiting:  # 是否为 asyncio.sleep 的 coro
                try:
                    await coro
                except asyncio.CancelledError:
                    return
            else:  # 执行
                try:
                    await coro
                except Exception as e:
                    traceback.print_exc()
                else:
                    now = datetime.now()
                    self.interval_offset = (now.microsecond / 1000000)
                    if self.is_disposable:
                        self.is_stop = True

    async def join(self, stop=False):
        if stop and not self.is_stop:
            self.is_stop = True

        if self.task:
            await self.task

    def stop(self):
        if not self.task.cancelled():
            self.task.cancel()
