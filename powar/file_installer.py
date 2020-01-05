import logging
import os
import sys
import subprocess
import jinja2

from typing import TextIO, Dict

from powar.configuration import ModuleConfig, GlobalConfig
from powar.settings import AppSettings
from powar.file_discoverer import FileDiscoverer

logger: logging.Logger = logging.getLogger(__name__)

class InstallPathError(Exception):
    pass

class FileInstaller:
    _module_config: ModuleConfig
    _global_config: GlobalConfig
    _settings: AppSettings
    _directory: str
    _module_config_path: str
    _file_discoverer: FileDiscoverer

    def __init__(self,
                 module_config: ModuleConfig,
                 global_config: GlobalConfig,
                 directory: str,
                 app_settings: AppSettings,
                 file_discoverer: FileDiscoverer):
        self._module_config = module_config
        self._global_config = global_config
        self._settings = app_settings
        self._directory = directory
        self._file_discoverer = file_discoverer
        self._module_config_path = os.path.join(directory, app_settings.module_config_filename)


    def install_and_exec(self) -> None:
        files_to_update = { 
            source: dest for source, dest in self._module_config.install.items() \
                if self._file_discoverer.should_update(os.path.join(self._directory, source))
        } if not self._settings.first_run else self._module_config.install
        
        if not files_to_update and self._module_config.install:
            logger.info(f"No files to install/update for {self._directory}")
            return

        if self._settings.execute:
            self._run_exec("exec_before")

        self._install_files(files_to_update)

        if self._settings.execute:
            self._run_exec("exec_after")


    def _install_files(self, files: Dict[str, str]) -> None:
        for source, dest in files.items():
            full_source = os.path.join(self._directory, source)
            full_dest = os.path.expandvars(os.path.expanduser(dest))

            if not os.path.isabs(full_dest):
                raise InstallPathError(
                    f"install path needs to be absolute: {dest} (in {self._module_config_path})")

            with open(full_source, 'r') as source_stream:
                source_contents = source_stream.read()

            rendered = self._render_template(source_contents)

            with open(full_dest, 'w') as dest_stream:
                try:
                    if not self._settings.dry_run:
                        dest_stream.write(rendered)
                        dest_stream.write("\n")
                    logger.info(f"Done: {full_source} -> {full_dest}")

                except IOError as e:
                    logger.warn(f"Unable to write file {full_dest}, skipping.")


    def _run_exec(self, which: str):
        if not self._module_config[which]:
            return

        rendered = self._render_template(self._module_config[which])

        if not self._settings.dry_run:
            result = subprocess.run(rendered, shell=True, check=True, stderr=subprocess.STDOUT)

            if result.stdout:
                logger.info(result.stdout)

        logger.info(f"Ran: {which} for {self._module_config_path}")


    def _render_template(self, contents: str) -> str:
        tm = jinja2.Template(contents)
        rendered = tm.render(**{
            **self._module_config.variables,
            **self._global_config.variables 
        })
        return rendered



