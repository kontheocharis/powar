from __future__ import annotations
import logging
import types
import os
import sys
from typing import Tuple, Iterable, Optional, Set, List, Dict, Any, Union
from getpass import getuser
from pwd import getpwuid
import subprocess

from powar.global_config import GlobalConfig
from powar.settings import AppSettings
from powar.util import saved_sys_properties, render_template, realpath, read_header, run_command, UserError

logger: logging.Logger = logging.getLogger(__name__)


class ModuleConfigApi:
    opts: Dict[Any, Any]
    local: Dict[Any, Any]

    _man: ModuleConfigManager

    def __init__(self, man: ModuleConfigManager, opts: Dict[Any, Any],
                 local: Dict[Any, Any]):
        self.opts = opts
        self.local = local
        self._man = man

    def install(self, entries: Union[Set[Tuple[str, str]], Dict[str,
                                                                str]]) -> None:
        '''
        Install files
        '''
        if isinstance(entries, set):
            self._man.install_entries(entries)
        elif isinstance(entries, dict):
            self._man.install_entries(entries.items())
        else:
            raise TypeError(
                f"invalid argument type to install: {type(entries)}")

    def execute(self, command: str, stdin=Optional[str]) -> str:
        '''
        Run command and return stdout if any
        '''
        return self._man.execute_command(command, stdin)

    def render(self, x: str) -> str:
        '''
        Render jinja templated string and return it
        '''
        return self._man.render_template(x)


class ModuleConfigManager:
    _directory: str
    _settings: AppSettings
    _global_config: GlobalConfig
    _api: ModuleConfigApi

    _current_user: str = getuser()

    _opts: Dict[Any, Any]
    _local: Dict[Any, Any] = {}

    _module_name: str
    _config_path: str
    _header: Optional[Dict[Any, Any]] = None

    def __init__(
        self,
        directory: str,
        global_config: GlobalConfig,
        app_settings: AppSettings,
    ):
        self._directory = directory
        self._global_config = global_config
        self._settings = app_settings

        self._opts = global_config.opts

        self._module_name = os.path.basename(self._directory)
        self._config_path = os.path.join(self._directory,
                                         app_settings.module_config_filename)

    def run(self) -> None:
        self._ensure_depends_are_met()

        api = ModuleConfigApi(self, self._opts, self._local)

        module = types.ModuleType('powar')
        module.p = api  # type: ignore
        module.__file__ = self._config_path

        with open(self._config_path, 'rb') as f:
            source = f.read()

        code = compile(source, self._config_path, 'exec')

        # Save and restore sys variables
        # with saved_sys_properties():
        if self._directory not in sys.path:
            sys.path.insert(0, self._directory)
        exec(code, module.__dict__)

    def get_system_packages(self) -> List[str]:
        header = self._read_header()
        return header.get('system_packages', [])

    def install_entries(self, entries: Iterable[Tuple[str, str]]) -> None:
        dir_files = os.listdir(self._directory)

        for src, dest in entries:
            with open(os.path.join(self._directory, src), 'r') as f:
                src_contents = f.read()
            rendered = self.render_template(src_contents)
            self._install_file(src, dest, content=rendered)

    def execute_command(self, command: str, stdin: Optional[str]) -> str:
        stdout = ''
        if not self._settings.dry_run:
            stdout = run_command(command, self._directory, return_stdout=True)
        logger.info(f"Ran: {command} for {self._config_path}")
        return stdout

    def _ensure_depends_are_met(self) -> None:
        header = self._read_header()

        depends = header.get('depends')
        if not depends:
            return

        if self._module_name in depends:
            raise UserError(
                f"module \"{self._module_name}\" cannot depend on itself")

        missing = depends - set(self._global_config.modules)

        if missing:
            raise UserError(*(
                f"module \"{self._module_name}\" depends on \"{module}\", " \
                f"but this is not enabled" for module in missing
            ))

    def render_template(
        self,
        contents: str,
    ) -> str:
        return render_template(
            contents,
            variables={
                'local': self._local,
                **self._opts,
            },
            directory=self._directory,
        )

    def _read_header(self) -> Dict[Any, Any]:
        if self._header is None:
            self._header = read_header(self._config_path)
        return self._header

    def _install_file(self, src: str, dest: str, content: str) -> None:
        dest = realpath(dest)
        try:
            owner_of_dest = getpwuid(os.stat(dest).st_uid).pw_name
        except FileNotFoundError:
            owner_of_dest = getpwuid(os.stat(
                os.path.dirname(dest)).st_uid).pw_name

        command = ["tee", dest]

        if not owner_of_dest == self._current_user:
            if not self._settings.switch_to_root:
                logger.warn(
                    f"installing at \"{dest}\" requires to be in root mode, skipping"
                )
            command = ["sudo", "-E", *command]

        if not self._settings.dry_run:
            subprocess.run(command,
                           input=str.encode(content + '\n'),
                           check=True,
                           capture_output=True)
        logger.info(f"Done: {src} -> {dest}")