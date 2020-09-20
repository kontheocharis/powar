import argparse
import os
import logging
import time
import shutil
import sys
import subprocess
from typing import cast, Iterable

from powar.module_config import ModuleConfigManager
from powar.global_config import GlobalConfigManager, GlobalConfig
from powar.settings import AppSettings, AppMode, AppLogLevel
from powar.util import realpath, UserError

LOGGING_FORMAT = "%(levelname)s: %(message)s"
logger: logging.Logger

ROOT_FLAGS = ("--root", "-r")


def parse_args_into(app_settings: AppSettings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        help="don't modify any files, just show what would be done",
        action="store_true")

    parser.add_argument("--template-dir",
                        dest="template_dir",
                        help="use a custom directory for templates")

    parser.add_argument("--config-dir",
                        dest="config_dir",
                        help="use a custom directory for configuration")

    parser.add_argument(
        *ROOT_FLAGS,
        dest="switch_to_root",
        action="store_true",
        help=
        "run powar in sudo mode to be able to install files in places outside $HOME")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-q",
                       "--quiet",
                       help="supress output",
                       action="store_const",
                       dest="log_level",
                       const=AppLogLevel.QUIET)
    group.add_argument("-v",
                       "--verbose",
                       help="be verbose",
                       action="store_const",
                       dest="log_level",
                       const=AppLogLevel.VERBOSE)

    subparsers = parser.add_subparsers(help="mode to use",
                                       dest="mode command")

    # Install mode
    parser_install = subparsers.add_parser(
        "install",
        help="install specified modules (empty argument installs all modules)")
    parser_install.set_defaults(mode=AppMode.INSTALL)
    parser_install.add_argument(
        "modules_to_consider",
        nargs="*",
        metavar="MODULE",
        help="module(s) to install (empty argument installs all modules)")

    # List-packages mode
    parser_list = subparsers.add_parser(
        "list", help="list system packages required to install config files")
    parser_list.set_defaults(mode=AppMode.LIST_PACKAGES)
    parser_list.add_argument(
        "modules_to_consider",
        nargs="*",
        metavar="MODULE",
        help=
        "module(s) to list packages for (empty argument lists for all modules)"
    )

    # New module mode
    parser_new = subparsers.add_parser("new", help="create a new powar module")
    parser_new.set_defaults(mode=AppMode.NEW_MODULE)
    parser_new.add_argument("new_module_name",
                            metavar="MODULE_NAME",
                            help="name of the new module to be created")

    # Init mode
    parser_init = subparsers.add_parser(
        "init", help="create the folders required for powar")
    parser_init.set_defaults(mode=AppMode.INIT)

    parser.parse_args(namespace=app_settings)
    return parser


def run_init(app_settings: AppSettings) -> None:
    os.makedirs(app_settings.config_dir, exist_ok=True)
    global_config_path = os.path.join(app_settings.config_dir,
                                      app_settings.global_config_filename)

    if not os.path.exists(global_config_path):
        shutil.copy(
            os.path.join(app_settings.data_path,
                         app_settings.global_config_template_filename),
            global_config_path)
        print(f"{global_config_path} created.")
    else:
        logger.warn(f"{global_config_path} exists, skipping.")

    try:
        os.makedirs(app_settings.template_dir)
        print(f"{app_settings.template_dir}/ created.")
    except FileExistsError:
        logger.warn(f"{app_settings.template_dir} exists, skipping.")


def run_new_module(app_settings: AppSettings) -> None:
    if not os.path.exists(app_settings.template_dir):
        raise UserError(f"{app_settings.template_dir} doesn't exist.")

    module_dir = os.path.join(app_settings.template_dir,
                              cast(str, app_settings.new_module_name))
    try:
        os.makedirs(module_dir)
    except FileExistsError:
        raise UserError(f"{module_dir} already exists.")

    module_config_path = os.path.join(module_dir,
                                      app_settings.module_config_filename)
    shutil.copy(
        os.path.join(app_settings.data_path,
                     app_settings.module_config_template_filename),
        module_config_path)
    print(f"{module_config_path} created.")


def run_list_packages(app_settings: AppSettings,
                      module_directories: Iterable[str],
                      global_config: GlobalConfig) -> None:
    for directory in module_directories:
        manager = ModuleConfigManager(directory, global_config, app_settings)
        for package in manager.get_system_packages():
            print(f"{os.path.basename(directory)}:")
            print(package)
            print('\n')


def run_install(app_settings: AppSettings, module_directories: Iterable[str],
                global_config: GlobalConfig) -> None:
    for directory in module_directories:
        manager = ModuleConfigManager(directory, global_config, app_settings)
        manager.run()


def main() -> None:
    app_settings = AppSettings()
    parser = parse_args_into(app_settings)

    # set logging level from arguments
    logging.basicConfig(level=app_settings.log_level.into_logging_level(),
                        format=LOGGING_FORMAT)
    logger = logging.getLogger(__name__)

    # resolve $VARIABLES and ~, ensure absolute
    dirs_to_resolve = ("template_dir", "config_dir", "cache_dir")
    for var in dirs_to_resolve:
        app_settings[var] = realpath(app_settings[var])
        if not os.path.isabs(app_settings[var]):
            parser.error(f"{var} needs to be absolute")

    try:
        if app_settings.mode == AppMode.INIT:
            return run_init(app_settings)

        if app_settings.mode == AppMode.NEW_MODULE:
            return run_new_module(app_settings)

        # cache_man = CacheManager(app_settings.cache_dir)

        global_config = GlobalConfigManager(app_settings.config_dir,
                                            app_settings).get_global_config()

        directories = [
            os.path.join(app_settings.template_dir, module)
            for module in global_config.modules
        ]

        if app_settings.mode == AppMode.LIST_PACKAGES:
            return run_list_packages(app_settings, directories, global_config)

        # Main logic
        if app_settings.mode == AppMode.INSTALL:
            if not directories:
                return logger.info("No files to install, exiting.")

            return run_install(app_settings, directories, global_config)

    except UserError as error:
        for arg in error.args:
            logger.error(arg)
    return None
