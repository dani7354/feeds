import os

MAX_THREAD_COUNT = 8

CONFIG_PATH = os.getenv("CONFIG_PATH")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
