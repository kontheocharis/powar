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

    _files_to_update_cause_module_configs_changed: List[str] = []
    _global_config_changed: bool = False

    _last_update: float

    def __init__(self, app_settings: AppSettings, cache_man: CacheManager, global_config: GlobalConfig):
        self._settings = app_settings
        self._cache_man = cache_man
        self._global_config = global_config

        global_config_path = os.path.join(
                self._settings.config_dir,
                self._settings.global_config_filename)

        self._last_update = self._cache_man.get_last_run()

        if os.path.getmtime(global_config_path) > self._last_update:
            self._global_config_changed = True

        for mod in self._global_config.modules:

            module_path = os.path.join(
                self._settings.template_dir,
                mod,
                self._settings.module_config_filename)

            if os.path.getmtime(module_path) > self._last_update:
                files = glob.glob(os.path.join(
                    self._settings.template_dir,
                    mod) + f"/[!{self._settings.module_config_filename}]*")
                self._files_to_update_cause_module_configs_changed.extend(files)


    def get_all_dirs(self) -> List[str]:
        all_files = [
            os.path.join(self._settings.template_dir, mod) \
                for mod in self._global_config.modules
        ]

        return all_files


    def should_update(self, source: str) -> bool:
        if self._global_config_changed:
            return True
        
        if source in self._files_to_update_cause_module_configs_changed:
            return True

        return os.path.getmtime(source) > self._last_update
