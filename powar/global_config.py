import logging
import types
import os
import sys
from typing import Iterable, Optional, Set, List, Dict, Any, Union, Tuple
from getpass import getuser

from powar.settings import AppSettings
from powar.util import saved_sys_properties, read_header, run_command, RunCommandResult, realpath

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

    def modules(self, *modules: List[str]):
        self._man.set_modules(modules)

    def execute(
        self,
        command: str,
        stdin: Optional[str] = None,
        decode_stdout=True,
        wait=True,
    ) -> RunCommandResult:
        '''
        Run command and return stdout if any
        '''
        return self._man.execute_command(command, stdin, decode_stdout, wait)

    def read(self, filename: str, as_bytes=False) -> Union[str, bytes]:
        return self._man.read_file(filename, as_bytes)


class GlobalConfigManager:
    _directory: str
    _settings: AppSettings
    _api: GlobalConfigApi
    _modules: List = []

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

        self._global_config.modules = self._modules
        return self._global_config

    def execute_command(self, command: str, stdin: Optional[str],
                        decode_stdout: bool, wait: bool) -> RunCommandResult:
        result = RunCommandResult(stdout=None, code=0)
        if not self._settings.dry_run:
            result = run_command(command, self._directory, stdin,
                                 decode_stdout, wait)
        logger.info(
            f"Ran{'' if wait else ' (in bg)'}: {command} for {self._config_path}"
        )
        return result

    def read_file(self, filename: str, as_bytes: bool) -> Union[str, bytes]:
        return open(realpath(filename), 'rb' if as_bytes else 'r').read()

    def set_modules(self, modules: List[str]):
        self._modules = modules
