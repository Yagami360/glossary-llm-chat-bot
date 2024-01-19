import logging
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime
from logging import LogRecord, StreamHandler
from typing import List

from pythonjsonlogger import jsonlogger


class JsonFormatter(jsonlogger.JsonFormatter):
    def parse(self) -> List[str]:
        """https://docs.python.jp/3/library/logging.html"""
        return ["timestamp", "level", "name", "message"]

    def add_fields(
        self, log_record: OrderedDict, record: LogRecord, message_dict: dict
    ) -> None:
        self.json_ensure_ascii = False
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.utcnow().isoformat()

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def setup():
    if StreamHandler not in map(type, logging.getLogger().handlers):
        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setFormatter(JsonFormatter())
        logging.getLogger().addHandler(stream_handler)


def log_decorator(logger):
    def _logging(func):
        def _wrapper(*args, **kwds):
            start_time = time.time()
            logger.info("[{}] {}".format(func.__qualname__, "START"))
            logger.debug(
                "[{}] {} args={} kwds={}".format(func.__qualname__, "START", args, kwds)
            )

            rtn = func(*args, **kwds)
            elapsed_time = 1000 * (time.time() - start_time)
            logger.info(
                "[{}] {} elapsed_time [ms]={:.5f}".format(
                    func.__qualname__, "END", elapsed_time
                )
            )
            logger.debug(
                "[{}] {} elapsed_time [ms]={:.5f} return {}".format(
                    func.__qualname__, "END", elapsed_time, rtn
                )
            )
            return rtn

        return _wrapper

    return _logging


setup()
logger = logging.getLogger("glossary-lim-chat-bot")
logging.getLogger().setLevel(level=os.environ.get("LOG_LEVEL", "INFO"))

if os.environ['LOG_LEVEL'] == "DEBUG":
    if not os.path.isdir(".logs"):
        os.mkdir(".logs")
    logger_fh = logging.FileHandler(os.path.join(".logs", 'app.log'))
    logger.addHandler(logger_fh)
