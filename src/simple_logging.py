#!/usr/bin/env python

import time


def log(message: str, console: bool = False):
    logged_message = f'{time.asctime()}, {message}'
    if console:
        print(logged_message)
    with open('../logs.txt', 'a') as log_file:
        print(logged_message, file=log_file, flush=True)


def clear_log_file():
    with open('../logs.txt', 'w') as file:
        file.truncate(0)
