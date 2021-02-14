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
from powar.util import saved_sys_properties, render_template, realpath, read_header, run_command, UserError, RunCommandResult

logger: logging.Logger = logging.getLogger(__name__)


class ModuleConfigApi:
    opts: Dict[Any, Any]
    local: Dict[Any, Any]

    _man: 'ModuleConfigManager'

    def __init__(self, man: 'ModuleConfigManager', opts: Dict[Any, Any],
                 local: Dict[Any, Any]):
        self.opts = opts
        self.local = local
        self._man = man

    def depends(self, entries: Iterable[str]) -> None:
        self.ensure_depends_are_met(set(entries))

    def install(
        self,
        entries: Union[Set[Tuple[str, str]], Dict[str, str]],
    ) -> None:
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

    def link(
        self,
        entries: Union[Set[Tuple[str, str]], Dict[str, str]],
    ) -> None:
        '''
        Install files
        '''
        if isinstance(entries, set):
            self._man.link_entries(entries)
        elif isinstance(entries, dict):
            self._man.link_entries(entries.items())
        else:
            raise TypeError(f"invalid argument type to link: {type(entries)}")

    def install_bin(
        self,
        entries: Union[Set[Tuple[str, str]], Dict[str, str]],
    ) -> None:
        '''
        Install files
        '''
        if isinstance(entries, set):
            self._man.install_entries(entries, binary=True)
        elif isinstance(entries, dict):
            self._man.install_entries(entries.items(), binary=True)
        else:
            raise TypeError(
                f"invalid argument type to install_bin: {type(entries)}")

    def execute(
        self,
        command: str,
        stdin: Optional[str] = None,
        decode_stdout=True,
        wait=True,
    ) -> Union[int, Tuple[Union[str, bytes], int]]:
        '''
        Run command and return stdout if any
        '''
        return self._man.execute_command(command, stdin, decode_stdout, wait)

    def has(self, module: str) -> bool:
        return self._man.has_module(module)

    def read(self, filename: str, as_bytes=False) -> Union[str, bytes]:
        return self._man.read_file(filename, as_bytes)

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

    def has_module(self, module: str) -> bool:
        return module in self._global_config.modules

    def run(self) -> None:
        api = ModuleConfigApi(self, self._opts, self._local)

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

    def ensure_depends_are_met(self, depends: Set[str]) -> None:
        if self._module_name in depends:
            raise UserError(
                f"module \"{self._module_name}\" cannot depend on itself")

        missing = depends - set(self._global_config.modules)

        if missing:
            raise UserError(*(
                f"module \"{self._module_name}\" depends on \"{module}\", " \
                f"but this is not enabled" for module in missing
            ))

    def install_entries(self,
                        entries: Iterable[Tuple[str, str]],
                        binary=False) -> None:
        dir_files = os.listdir(self._directory)

        if binary:
            for src, dest in entries:
                self._install_bin(src, dest)
        else:
            for src, dest in entries:
                with open(os.path.join(self._directory, src), 'r') as f:
                    src_contents = f.read()
                rendered = self.render_template(src_contents)
                self._install_file(src, dest, content=rendered)

    def link_entries(
        self,
        entries: Iterable[Tuple[str, str]],
    ) -> None:
        for src, dest in entries:
            if not self._settings.dry_run:
                dest_dir = realpath(os.path.dirname(dest))
                dest_file = os.path.basename(dest)
                run_command(f'mkdir -p {dest_dir}', self._directory)
                run_command(f'ln -Fs {realpath(src)} ./{dest_file}', dest_dir)
            logger.info(f"Linked: {src} -> {dest}")

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

    def _can_install_without_root(self, dest: str) -> bool:
        try:
            owner_of_dest = getpwuid(os.stat(dest).st_uid).pw_name
        except FileNotFoundError:
            owner_of_dest = getpwuid(os.stat(
                os.path.dirname(dest)).st_uid).pw_name

        if not owner_of_dest == self._current_user:
            return False
        return True

    def _get_install_prefix(self, dest: str) -> str:
        prefix = ''
        if not self._can_install_without_root(dest):
            if not self._settings.switch_to_root:
                logger.warn(
                    f"installing at \"{dest}\" requires to be in root mode, skipping"
                )
                return
            prefix = 'sudo -E'
        return prefix

    def _install_file(self, src: str, dest: str, content: str) -> None:
        dest = realpath(dest)
        prefix = self._get_install_prefix(dest)

        if not self._settings.dry_run:
            run_command(f'{prefix} mkdir -p {os.path.dirname(dest)}',
                        self._directory)
            run_command(f'{prefix} cp {src} {dest}', self._directory)
            run_command(f'{prefix} tee {dest}',
                        self._directory,
                        stdin=str.encode(content + '\n'))
        logger.info(f"Done: {src} -> {dest}")

    def _install_bin(self, src: str, dest: str) -> None:
        dest = realpath(dest)
        prefix = self._get_install_prefix(dest)

        if not self._settings.dry_run:
            run_command(f'{prefix} mkdir -p {os.path.dirname(dest)}',
                        self._directory)
            run_command(f'{prefix} cp {src} {dest}', self._directory)
        logger.info(f"Done (bin): {src} -> {dest}")
