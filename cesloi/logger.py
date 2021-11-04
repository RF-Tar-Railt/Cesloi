import loguru
import time


class Logger:
    logger: loguru.logger = loguru.logger

    def __init__(self, level='INFO'):
        self.logger.add('bot_running_log_' + time.strftime("%Y-%m-%d", time.localtime()) + '.log',
                        format="{time}|{level}|{message}", level=level, enqueue=True)
        self.logger.info("--------------------------------------------------------------------")
