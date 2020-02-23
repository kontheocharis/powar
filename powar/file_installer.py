import logging
import os
from typing import Tuple, List, Iterator, Union

from powar.configuration import ModuleConfig, GlobalConfig
from powar.settings import AppSettings, AppMode
from powar.module_discoverer import ModuleDiscoverer
from powar.util import realpath, UserError, run_command, render_template

logger: logging.Logger = logging.getLogger(__name__)

class FileInstaller:
    _module_config: ModuleConfig
    _global_config: GlobalConfig
    _settings: AppSettings
    _directory: str
    _module_config_path: str
    _module_name: str
    _module_discoverer: ModuleDiscoverer

    def __init__(self,
                 module_config: ModuleConfig,
                 global_config: GlobalConfig,
                 directory: str,
                 app_settings: AppSettings,
                 module_discoverer: ModuleDiscoverer):
        self._module_config = module_config
        self._global_config = global_config
        self._settings = app_settings
        self._directory = directory
        self._module_discoverer = module_discoverer
        self._module_config_path = os.path.join(directory, app_settings.module_config_filename)
        self._module_name = os.path.basename(directory)
        assert self._module_name != ''


    def install_and_exec(self) -> None:
        self._ensure_deps_are_met()

        files_to_update = list(self._get_files_to_update())

        if self._module_config.install and not files_to_update:
            logger.info(f"No files to install/update for {self._directory}")
            return

        if self._settings.execute and self._module_config.exec_before is not None:
            self._run_exec(self._module_config.exec_before)

        self._install_files(files_to_update)

        if self._settings.execute and self._module_config.exec_after is not None:
            self._run_exec(self._module_config.exec_after)

    def _get_files_to_update(self) -> Iterator[Tuple[str, str]]:
        dir_files = os.listdir(self._directory)

        for source, dest in self._module_config.install.items():
            if source not in dir_files:
                raise UserError(f"file \"{source}\" is not in directory {self._directory}")

            real_dest = realpath(dest)
            if not os.path.isabs(real_dest):
                raise UserError(
                    f"install path needs to be absolute: {dest} (in {self._module_config_path})")

            full_source = os.path.join(self._directory, source)

            if self._settings.mode == AppMode.INSTALL \
                    or self._module_discoverer.should_update(full_source):

                yield full_source, real_dest


    def _install_files(self, files: Iterator[Tuple[str, str]]) -> None:
        for source, dest in files:
            with open(source, "r") as source_stream:
                source_contents = source_stream.read()

            rendered, external_installs = self._render_template(
                source_contents, external_installs=True)

            self._install_file(source, dest, content=rendered)

            for ext_filename, ext_content in external_installs:
                ext_dest = os.path.join(os.path.dirname(dest), ext_filename)
                ext_source = f"{source} (external {ext_filename})"
                self._install_file(ext_source, ext_dest, ext_content)


    def _install_file(self, source: str, dest: str, content: str) -> None:
        with open(dest, "w") as stream:
            try:
                if not self._settings.dry_run:
                    stream.write(content)
                    stream.write("\n")
                logger.info(f"Done: {source} -> {dest}")

            except IOError:
                logger.warning(f"Unable to write file {dest}, skipping.")


    def _run_exec(self, command: str, config_item=False) -> None:
        rendered = self._render_template(command)

        if config_item:
            return run_command(command, self._directory, return_stdout=True)

        elif not self._settings.dry_run:
            run_command(command, self._directory, return_stdout=False)
            logger.info(f"Ran: {command} for {self._module_config_path}")


    def _render_template(self,
                         contents: str,
                         external_installs=False
                         ) -> Union[str, Tuple[str, List[Tuple[str, str]]]]:
        return render_template(
            contents,
            variables={**self._module_config.variables,
                       **self._global_config.variables},
            directory=self._directory,
            external_installs=external_installs)


    def _ensure_deps_are_met(self) -> None:
        if self._module_name in self._module_config.depends:
            raise UserError(f"module \"{self._module_name}\" cannot depend on itself")

        missing = set(self._module_config.depends) - set(self._global_config.modules)

        if missing:
            raise UserError(*(f"module \"{self._module_name}\" depends on \"{module}\", " \
                              f"but this is not enabled" for module in missing))
