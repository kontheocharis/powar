import os
import logging
from typing import List

from powar.settings import AppSettings
from powar.configuration import GlobalConfig
from powar.cache import CacheManager


logger: logging.Logger = logging.getLogger(__name__)

class ModuleDiscoverer:
    _settings: AppSettings
    _cache_man: CacheManager
    _global_config: GlobalConfig

    _files_to_update_cause_module_configs_changed: List[str] = []
    _global_config_changed: bool = False

    _last_update: float

    def __init__(self,
                 app_settings: AppSettings,
                 cache_man: CacheManager,
                 global_config: GlobalConfig):
        self._settings = app_settings
        self._cache_man = cache_man
        self._global_config = global_config

        global_config_path = os.path.join(
            self._settings.config_dir,
            self._settings.global_config_filename)

        self._last_update = self._cache_man.get_last_run()

        if os.path.getmtime(global_config_path) > self._last_update:
            self._global_config_changed = True

        for module in self._global_config.modules:
            if self._settings.modules_to_consider and module not in self._settings.modules_to_consider:
                continue

            module_path = os.path.join(self._settings.template_dir, module)
            module_config_path = os.path.join(
                module_path, self._settings.module_config_filename)

            if os.path.getmtime(module_config_path) > self._last_update:

                files = (os.path.join(module_path, filename) \
                         for filename in os.listdir(module_path) \
                         if filename != self._settings.module_config_filename)

                self._files_to_update_cause_module_configs_changed.extend(files)


    def get_all_dirs(self) -> List[str]:
        return [os.path.join(self._settings.template_dir, module) \
                for module in self._global_config.modules \
                if not self._settings.modules_to_consider or module in self._settings.modules_to_consider ]


    def should_update(self, source: str) -> bool:
        return self._global_config_changed \
            or source in self._files_to_update_cause_module_configs_changed \
            or os.path.getmtime(source) > self._last_update
