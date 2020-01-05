import os
import glob
import logging
import sys

from powar.settings import AppSettings
from powar.configuration import GlobalConfig
from powar.cache import CacheManager

from typing import List

logger: logging.Logger = logging.getLogger(__name__)

class FileDiscoverer:
    _settings: AppSettings
    _cache_man: CacheManager
    _global_config: GlobalConfig

    def __init__(self, app_settings: AppSettings, cache_man: CacheManager, global_config: GlobalConfig):
        self._settings = app_settings
        self._cache_man = cache_man
        self._global_config = global_config

    def get_all_dirs(self) -> List[str]:
        all_files = [
            os.path.join(self._settings.template_dir, mod) \
                for mod in self._global_config.modules
        ]

        return all_files

    def should_update(self, source: str) -> bool:
        last_update = self._cache_man.get_last_run()
        return os.path.getmtime(source) > last_update
