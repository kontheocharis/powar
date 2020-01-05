import argparse
import yaml
import os
import logging
import sys
import time
import dataclasses

from powar.configuration import ModuleConfig, GlobalConfig
from powar.file_installer import FileInstaller
from powar.file_discoverer import FileDiscoverer
from powar.settings import AppSettings
from powar.cache import CacheManager
from powar.util import realpath

from typing import Dict, List, Final

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger: logging.Logger = logging.getLogger(__name__)

def main():
    app_settings = AppSettings()

    parser = argparse.ArgumentParser()

    parser.add_argument("--template-dir", dest='template_dir',
                        help="use a custom directory for templates")

    parser.add_argument("--config-dir", dest='config_dir',
                        help="use a custom directory for configuration")

    parser.add_argument("--dry-run", dest='dry_run',
                        help="don't modify any files, just show what would be done",
                        action='store_true')

    parser.add_argument("--first-run", dest='first_run',
                        help="run for the first time",
                        action='store_true')

    parser.add_argument("--no-exec", dest='execute',
                        help="do not execute any exec-* fields in modules",
                        action='store_false')

    parser.add_argument("--list-packages", dest='list_packages',
                        help="only list system packages required to install chosen config files",
                        action='store_true')

    args = parser.parse_args()
    app_settings = dataclasses.replace(
        app_settings, **{ k: v for k, v in vars(args).items() if v is not None })

    # resolve $VARIABLES and ~, ensure absolute
    dirs_to_resolve = ['template_dir', 'config_dir', 'cache_dir']
    for d in dirs_to_resolve:
        app_settings[d] = realpath(app_settings[d])
        if not os.path.isabs(app_settings[d]):
            parser.error(f"{d} needs to be absolute")

    cache_man = CacheManager(app_settings.cache_dir)

    global_config = GlobalConfig.from_yaml_path(
            app_settings.config_dir, app_settings.global_config_filename)

    file_discoverer = FileDiscoverer(app_settings, cache_man, global_config)

    dirs = file_discoverer.get_all_dirs()

    # If we only need to list packages
    if app_settings.list_packages:
        for d in dirs:
            config = ModuleConfig.from_yaml_path(d, app_settings.module_config_filename)
            for p in config.system_packages:
                print(p)

    else:
        if len(dirs) == 0:
            logger.info("No new or modified files to install, exiting.")
            sys.exit()

        for d in dirs:
            config = ModuleConfig.from_yaml_path(d, app_settings.module_config_filename)
            installer = FileInstaller(config, global_config, d, app_settings, file_discoverer)
            installer.install_and_exec()

        cache_man.set_last_run(time.time())
