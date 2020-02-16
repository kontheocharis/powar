import logging
import os
import subprocess
from typing import Tuple, List, Iterator, Union
import jinja2

from powar.configuration import ModuleConfig, GlobalConfig
from powar.settings import AppSettings
from powar.file_discoverer import FileDiscoverer
from powar.util import realpath, UserError
from powar.jinja_ext import ExternalExtension


logger: logging.Logger = logging.getLogger(__name__)

class FileInstaller:
    _module_config: ModuleConfig
    _global_config: GlobalConfig
    _settings: AppSettings
    _directory: str
    _module_config_path: str
    _module_name: str
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
        self._module_name = os.path.basename(directory)
        assert self._module_name != ''


    def install_and_exec(self) -> None:
        self._ensure_deps_are_met()

        files_to_update = list(self._get_files_to_update())

        if self._module_config.install and not files_to_update:
            logger.info(f"No files to install/update for {self._directory}")
            return

        if self._settings.execute:
            self._run_exec("exec_before")

        self._install_files(files_to_update)

        if self._settings.execute:
            self._run_exec("exec_after")

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

            if self._settings.first_run \
                    or self._file_discoverer.should_update(full_source):

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


    def _run_exec(self, which: str) -> None:
        command = self._module_config.get(which)
        if command is None:
            return

        rendered = self._render_template(command)

        if not self._settings.dry_run:
            result = subprocess.run(
                rendered, shell=True, check=True,
                stderr=subprocess.STDOUT, cwd=self._directory)

            if result.stdout:
                logger.info(result.stdout)

        logger.info(f"Ran: {which} for {self._module_config_path}")


    def _render_template(self,
                         contents: str,
                         external_installs=False
                         ) -> Union[str, Tuple[str, List[Tuple[str, str]]]]:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._directory))

        if external_installs:
            env.add_extension(ExternalExtension)

        template = env.from_string(contents)

        rendered = template.render({
            **self._module_config.variables,
            **self._global_config.variables
        })

        if external_installs:
            return rendered, env.external_installs

        return rendered

    def _ensure_deps_are_met(self) -> None:
        if self._module_name in self._module_config.depends:
            raise UserError(f"module \"{self._module_name}\" cannot depend on itself")

        missing = set(self._module_config.depends) - set(self._global_config.modules)

        if missing:
            raise UserError(*(f"module \"{self._module_name}\" depends on \"{module}\", " \
                              f"but this is not enabled" for module in missing))
