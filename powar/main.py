import argparse
import os
import logging
import time

from powar.configuration import ModuleConfig, GlobalConfig
from powar.file_installer import FileInstaller
from powar.module_discoverer import ModuleDiscoverer
from powar.settings import AppSettings
from powar.cache import CacheManager
from powar.util import realpath, UserError


LOGGING_FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format=LOGGING_FORMAT)
logger: logging.Logger = logging.getLogger(__name__)

def main():
    app_settings = AppSettings()

    parser = argparse.ArgumentParser()

    parser.add_argument("--template-dir", dest="template_dir",
                        help="use a custom directory for templates")

    parser.add_argument("--config-dir", dest="config_dir",
                        help="use a custom directory for configuration")

    parser.add_argument("--dry-run", dest="dry_run",
                        help="don't modify any files, just show what would be done",
                        action="store_true")

    parser.add_argument("--first-run", dest="first_run",
                        help="run for the first time",
                        action="store_true")

    parser.add_argument("--no-exec", dest="execute",
                        help="do not execute any exec-* fields in modules",
                        action="store_false")

    parser.add_argument("--list-packages", dest="list_packages",
                        help="only list system packages required to install chosen config files",
                        action="store_true")

    parser.parse_args(namespace=app_settings)

    # resolve $VARIABLES and ~, ensure absolute
    dirs_to_resolve = ["template_dir", "config_dir", "cache_dir"]
    for var in dirs_to_resolve:
        app_settings[var] = realpath(app_settings[var])
        if not os.path.isabs(app_settings[var]):
            parser.error(f"{var} needs to be absolute")

    try:
        cache_man = CacheManager(app_settings.cache_dir)

        global_config = GlobalConfig.from_yaml_path(
            app_settings.config_dir, app_settings.global_config_filename)

        module_discoverer = ModuleDiscoverer(app_settings, cache_man, global_config)

        directories = module_discoverer.get_all_dirs()

        if app_settings.list_packages:
            for directory in directories:
                config = ModuleConfig.from_yaml_path(directory, app_settings.module_config_filename)
                for package in config.system_packages:
                    print(package)
            return

        if len(directories) == 0:
            logger.info("No new or modified files to install, exiting.")
            return

        # Main logic
        for directory in directories:
            config = ModuleConfig.from_yaml_path(directory, app_settings.module_config_filename)
            installer = FileInstaller(
                config, global_config, directory, app_settings, module_discoverer)
            installer.install_and_exec()

        cache_man.set_last_run(time.time())

    except UserError as error:
        for arg in error.args:
            logger.error(arg)
