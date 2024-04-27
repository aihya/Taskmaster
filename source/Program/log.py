import datetime
from sys import stderr


def log(message):
    with open("./log.txt", "a") as file:
        current_time = str(datetime.datetime.now())
        file.write(f"[{current_time}]: {message}\n")


# class default
# class Logger:
#     sink = None

#     def __init__(self, sink) -> None:
#         if sink != "stderr":
#             self.sink = open(sink
#         else:
#             self.sink = stderr

#     def log(message):
#         current_time = str(datetime.datetime.now())
#         print()
