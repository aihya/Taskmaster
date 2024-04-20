import datetime

def log(message):
    with open('./log.txt', 'a') as file:
        current_time = str(datetime.datetime.now())
        file.write(f"[{current_time}]: {message}\n")
