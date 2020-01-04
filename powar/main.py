import argparse
import yaml
import os
import shutil
import logging
import dataclasses

from typing import Dict, List, Final
from powar.configuration import ModuleConfig
from powar.file_installer import FileInstaller
from powar.settings import AppSettings

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

    args = parser.parse_args()
    app_settings = dataclasses.replace(
        app_settings, **{ k: v for k, v in vars(args).items() if v is not None })

    print(dataclasses.asdict(app_settings))

    # config = ModuleConfig.from_yaml_path(args.directory, app_settings.module_config_filename)

    # installer = FileInstaller(config, args.directory, app_settings)
    # installer.install_files()
