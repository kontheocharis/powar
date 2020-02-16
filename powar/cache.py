import os

class CacheManager:
    _last_run_path: str
    _last_run_cached: float = None
    _cache_path: str

    def __init__(self, cache_path: str):
        self._cache_path = cache_path
        self._last_run_path = os.path.join(cache_path, "last_run")

    def get_last_run(self) -> float:
        if self._last_run_cached is not None:
            return self._last_run_cached

        os.makedirs(self._cache_path, exist_ok=True)
        with open(self._last_run_path, "a+") as last_run_file:
            last_run_file.seek(0)
            contents = last_run_file.read()

        self._last_run_cached = float(contents) if contents else 0.0
        return self._last_run_cached

    def set_last_run(self, last_run: float) -> None:
        with open(self._last_run_path, "w") as last_run_file:
            last_run_file.write(str(last_run))
        self._last_run_cached = last_run
