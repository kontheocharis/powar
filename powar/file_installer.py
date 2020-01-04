import logging
import os
import sys
import shutil
import jinja2

from typing import TextIO

from powar.configuration import ModuleConfig
from powar.settings import AppSettings

logger: logging.Logger = logging.getLogger(__name__)

class InstallPathError(Exception):
    pass

class FileInstaller:

    # Local module configuration
    config: ModuleConfig
    
    # Global app settings
    settings: AppSettings

    # Directory to look for source files relative to
    directory: str

    def __init__(self, config: ModuleConfig, directory: str, settings: AppSettings):
        self.config = config
        self.settings = settings
        self.directory = directory

    def install_files(self) -> None:
        for source, dest in self.config.install.items():
            full_source = os.path.join(self.directory, source)
            full_dest = os.path.expandvars(os.path.expanduser(dest))

            if not os.path.isabs(full_dest):
                raise InstallPathError(
                    f"Install path needs to be absolute: {dest} (in {os.path.join(directory, self.settings.module_config_filename)})")

            with open(full_source, 'r') as source_stream:
                source_contents = source_stream.read()

            rendered = self._render_template(source_contents)

            with open(full_dest, 'w') as dest_stream:
                try:
                    if not self.app_settings.dry_run:
                        dest_stream.write(rendered)
                    logger.info(f"Done: {full_source} -> {full_dest}")

                except IOError as e:
                    logger.warn(f"Unable to write file {full_dest}, skipping.")


    def _render_template(self, contents: str):
        tm = jinja2.Template(contents)
        rendered = tm.render(foo="bar")
        return rendered
