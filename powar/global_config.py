import logging
import types
import os
import sys
from typing import Iterator, Optional, Set, List, Dict, Any, Union
from getpass import getuser

from powar.settings import AppSettings
from powar.util import saved_sys_properties, read_header, run_command

logger: logging.Logger = logging.getLogger(__name__)


class GlobalConfig:
    modules: List[str]
    opts: Dict[Any, Any] = {}


class GlobalConfigApi:
    opts: Dict[Any, Any]

    _man: 'GlobalConfigManager'

    def __init__(self, man: 'GlobalConfigManager', opts: Dict[Any, Any]):
        self.opts = opts
        self._man = man

    def execute(
        self,
        command: str,
        stdin=Optional[str],
        return_stdout=False,
        decode_stdout=True,
        wait=True,
    ) -> Optional[Union[str, bytes]]:
        '''
        Run command and return stdout if any
        '''
        return self._man.execute_command(command, stdin, return_stdout,
                                         decode_stdout, wait)


class GlobalConfigManager:
    _directory: str
    _settings: AppSettings
    _api: GlobalConfigApi

    _global_config: GlobalConfig = GlobalConfig()

    _config_path: str
    _header: Optional[Dict[Any, Any]] = None

    def __init__(
        self,
        directory: str,
        app_settings: AppSettings,
    ):
        self._directory = directory
        self._settings = app_settings

        self._config_path = os.path.join(self._directory,
                                         app_settings.global_config_filename)

    def get_global_config(self) -> GlobalConfig:
        api = GlobalConfigApi(self, self._global_config.opts)

        module = types.ModuleType('powar')
        module.p = api  # type: ignore
        module.__file__ = self._config_path

        with open(self._config_path, 'rb') as f:
            source = f.read()

        code = compile(source, self._config_path, 'exec')

        # Save and restore sys variables and cwd
        old_cwd = os.getcwd()
        with saved_sys_properties():
            if self._directory not in sys.path:
                sys.path.insert(0, self._directory)
            os.chdir(self._directory)
            exec(code, module.__dict__)
            os.chdir(old_cwd)

        self._global_config.modules = self._get_modules()
        return self._global_config

    def execute_command(self, command: str, stdin: Optional[str],
                        return_stdout: bool, decode_stdout: bool,
                        wait: bool) -> Optional[Union[str, bytes]]:
        stdout = None
        if not self._settings.dry_run:
            stdout = run_command(command, self._directory, return_stdout,
                                 decode_stdout, wait)
        logger.info(f"Ran: {command} for {self._config_path}")
        return stdout

    def _read_header(self) -> Dict[Any, Any]:
        if self._header is None:
            self._header = read_header(self._config_path)
        return self._header

    def _get_modules(self) -> List[str]:
        header = self._read_header()
        return header.get('modules', [])
