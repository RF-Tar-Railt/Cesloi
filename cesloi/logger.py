import loguru
import time


class Logger:
    logger: loguru.logger = loguru.logger

    def __init__(self, level='INFO'):
        self.logger.add('bot_running_log_' + time.strftime("%Y-%m-%d", time.localtime()) + '.log',
                        format="{time}|{level}|{message}", level=level, enqueue=True,
                        rotation="500MB", encoding="utf-8")
        self.logger.info("--------------------------------------------------------------------")
