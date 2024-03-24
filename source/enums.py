from enum import IntEnum
import signal


class Signals(IntEnum):
    TERM = signal.SIGTERM
    HUP = signal.SIGHUP
    INT = signal.SIGINT
    QUIT = signal.SIGQUIT
    KILL = signal.SIGKILL
    USR1 = signal.SIGUSR1
    USR2 = signal.SIGUSR2

    @classmethod
    def from_str(cls, value):
        value = value.upper()
        for k, v in cls.__members__.items():
            if k == value:
                return v
        else:
            raise ValueError(
                f"Signal should be one of the following values {Signals.__members__.keys}"
            )


class AutoRestart(IntEnum):
    NEVER = 0
    UNEXPECTED = 1
    ALWAYS = 2

    @classmethod
    def from_str(cls, value):
        value = value.upper()
        for k, v in cls.__members__.items():
            if k == value:
                return v
        else:
            raise ValueError(
                f"Auto retart should be one of the following values {AutoRestart.__members__.keys}"
            )


class ProcessStatusEnum(IntEnum):
    NOT_LAUNCH = 0
    RUNNING = 1
    STOP_OK = 2
    STOP_KO = 3
