from time import sleep
from random import randint

def humanise(min, max = None):
    if max:
        sleep_time = randint(min, max)
    else: sleep_time = min
    sleep(sleep_time)