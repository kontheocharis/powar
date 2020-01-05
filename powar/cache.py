import os

from typing import TextIO

class CacheManager:
    _last_run_path: str

    def __init__(self, cache_path: str):
        self._last_run_path = os.path.join(cache_path, "last_run")

    def get_last_run(self) -> float:
        with open(self._last_run_path, "r") as last_run_file:
            contents = last_run_file.read()
        if not contents:
            return 0.0
        else:
            return float(contents)

    def set_last_run(self, last_run: float) -> None:
        with open(self._last_run_path, "w") as last_run_file:
            last_run_file.write(str(last_run))
