import datetime
from sys import stderr


import syslog
import datetime


class Logger:
    _instance = None

    def __new__(cls, log_identifier="Taskmaster"):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.log_identifier = log_identifier
        return cls._instance

    def log(self, message, log_level=syslog.LOG_INFO):
        syslog.openlog(self.log_identifier)
        syslog.syslog(log_level, message)


logger = Logger()
