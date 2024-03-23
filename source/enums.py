from enum import IntEnum
import signal

class Signals(IntEnum):
	TERM = signal.SIGTERM
	HUP  = signal.SIGHUP
	INT  = signal.SIGINT
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
			raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")

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
			raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")

class ProcessStatusEnum(IntEnum):
	NOT_LAUNCH = 0
	RUNNING = 1
	STOP_OK = 2
	STOP_KO = 3