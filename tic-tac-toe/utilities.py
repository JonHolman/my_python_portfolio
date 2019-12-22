#!/usr/bin/env python

# imports to support clearing the screen
from subprocess import call
import os


def clear():
    _ = call('clear' if os.name == 'posix' else 'cls')


def is_an_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    pass
