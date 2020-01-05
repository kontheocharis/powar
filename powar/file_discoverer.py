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

    def __init__(self, app_settings: AppSettings, cache_man: CacheManager):
        self._settings = AppSettings
        self._cache_man = CacheManager

    def get_dirs_to_update(self) -> List[str]:
        all_files = glob.glob(
            os.path.join(self._settings.config_dir, "/**/", self._settings.module_config_filename),
            recursive=True)

        if self._settings.first_run:
            return [os.path.dirname(f) for f in all_files]

        last_update = self._cache_man.get_last_run()
        files_to_update = []

        for file in all_files:
            file_updated_time = os.path.getmtime(file)

            if file_updated_time > last_update:
                files_to_update.append(file)

        return [os.path.dirname(f) for f in files_to_update]
