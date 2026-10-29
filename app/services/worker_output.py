"""Silence private worker output at both Python and native-library boundaries."""
import os
import sys


def silence_worker_output():
    # Windows console streams retain their original handles after dup2.
    # Replace those wrappers as well so interpreter shutdown can flush safely.
    stdout = open(os.devnull, 'w', encoding='utf-8')
    stderr = open(os.devnull, 'w', encoding='utf-8')
    os.dup2(stdout.fileno(), 1)
    os.dup2(stderr.fileno(), 2)
    sys.stdout = sys.__stdout__ = stdout
    sys.stderr = sys.__stderr__ = stderr
