from datetime import datetime, timedelta
from typing import Dict, Union
import abc


class Timer(abc.ABC):
    type: str
    interval: Dict[str, Union[int, float]] = {}

    @abc.abstractmethod
    def get_delta(self):
        pass


class EveryTimer(Timer):
    """
    从机器人启动时计时
    """
    type: str = 'every'

    def __init__(self, **kwargs):
        if kwargs:
            self.interval = kwargs
        else:
            self.every_minute()

    def get_delta(self):
        while True:
            yield datetime.now() + timedelta(**self.interval)

    def every_second(self):
        """每秒执行一次
        """
        self.interval = {"seconds": 1}
        return self

    def every_custom_seconds(self, seconds: int):
        """每 seconds 秒执行一次

        Args:
            seconds (int): 距离下一次执行的时间间隔, 单位为秒
        """
        self.interval = {"seconds": seconds}
        return self

    def every_minute(self):
        """每分钟执行一次
        """
        self.interval = {'minutes': 1}
        return self

    def every_custom_minutes(self, minutes: int):
        """每 minutes 分钟执行一次

        Args:
            minutes (int): 距离下一次执行的时间间隔, 单位为分
        """
        self.interval = {"seconds": minutes}
        return self

    def every_hour(self):
        """每小时执行一次
        """
        self.interval = {'hours': 1}
        return self

    def every_custom_hours(self, hours: int):
        """每 hours 小时执行一次

        Args:
            hours (int): 距离下一次执行的时间间隔, 单位为小时
        """
        self.interval = {'hours': hours}
        return self

    def every_week(self):
        """每隔一周执行一次
        """
        self.interval = {'weeks': 1}
        return self

    def every_custom_weeks(self, weeks: int):
        """每 weeks 周执行一次

        Args:
            weeks (int): 距离下一次执行的时间间隔, 单位为周
        """
        self.interval = {'weeks': weeks}
        return self

    def every_day(self):
        """每隔一天执行一次
        """
        self.interval = {'days': 1}
        return self

    def every_custom_days(self, days: int):
        """每 days 天执行一次

        Args:
            days (int): 距离下一次执行的时间间隔, 单位为天
        """
        self.interval = {'days': days}
        return self


class RouteTimer(Timer):
    """
    从对应的0时刻开始计时
    """
    type: str = 'route'

    def get_delta(self):
        while True:
            yield self._start_time()

    def __init__(self, **kwargs):
        if kwargs:
            self.interval = kwargs

    def route_second(self, seconds: int):
        """在每分钟的第 seconds 秒执行一次

        Args:
            seconds (int): 距离下一次执行的时间间隔, 单位为秒
        """
        if seconds > 60 or seconds < 0:
            raise ValueError
        self.interval['seconds'] = seconds
        return self

    def route_minutes(self, minutes: int):
        """在每小时的第 minutes 分执行一次

        Args:
            minutes (int): 距离下一次执行的时间间隔, 单位为分
        """
        if minutes > 60 or minutes < 0:
            raise ValueError
        self.interval['minutes'] = minutes
        return self

    def route_hours(self, hours: int):
        """在每天的第 hours 时执行一次

        Args:
            hours (int): 距离下一次执行的时间间隔, 单位为时
        """
        if hours > 24 or hours < 0:
            raise ValueError
        self.interval['hours'] = hours
        return self

    def route_weekdays(self, weekday: int):
        """在每周的星期 weekday 执行一次

        Args:
            weekday (int): 星期几，从monday = 1开始算起
        """
        if weekday > 7 or weekday < 0:
            raise ValueError
        self.interval['weeks'] = weekday / 7
        return self

    def route_days(self, days: int):
        """在每月的 days 号执行一次

        Args:
            days (int): 距离下一次执行的时间间隔, 单位为天
        """
        if days > 31 or days < 0:
            raise ValueError
        self.interval['days'] = days
        return self

    def _start_time(self):
        now = datetime.now()
        year = now.year
        month = now.month
        weekday = now.weekday()
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second
        for k, v in self.interval.items():
            if k == 'seconds':
                if v - second < 0:
                    minute += 1
                second = v
            if k == 'minutes':
                if v - minute < 0:
                    hour += 1
                minute = v
                second = 0
            if k == 'hours':
                if v - hour < 0:
                    day += 1
                hour = v
                minute = 0
                second = 0

            if k == 'weeks':
                hour = 0
                minute = 0
                second = 0
                day += 6 - weekday

            if k == 'days':
                if v - day < 0:
                    month += 1
                day = v
                hour = 0
                minute = 0
                second = 0
        return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


class SpecialTimer(Timer):
    """
    直到一年中一个特定的时间才执行
    """

    def __init__(self, **kwargs):
        if kwargs:
            self.interval = kwargs

    def get_delta(self):
        while True:
            yield self._start_time()

    def set_special_day(
            self,
            month: int,
            day: int,
            hour: int = 0,
            minute: int = 0,
            second: int = 0
    ):
        self.interval = {'month': month, 'day': day, 'hour': hour, 'minute': minute, 'second': second}
        return self

    def _start_time(self):
        now = datetime.now()
        year = now.year
        if self.interval['month'] < now.month:
            year += 1
        return datetime(year=year, **self.interval)


if __name__ == "__main__":
    import asyncio

    a = RouteTimer().route_second(7)
    print(a._start_time() + timedelta(**a.interval))
    c = (a._start_time() + timedelta(**a.interval) - datetime.now()).total_seconds()
    print(c)
    asyncio.run(asyncio.sleep(c))
    print(datetime.now())

    b = EveryTimer().every_custom_seconds(20)
    d = (datetime.now() + timedelta(**b.interval) - datetime.now()).total_seconds()
    print(d)
    asyncio.run(asyncio.sleep(d))
    print(datetime.now())

    c = SpecialTimer().set_special_day(12, 1, 12)
    print(c._start_time() - datetime.now())
