import os

from abc import ABC


class Subscriptable(ABC):
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


class UserError(Exception):
    pass


def realpath(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))
