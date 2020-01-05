import os

def realpath(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))
