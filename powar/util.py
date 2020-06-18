import os
import sys
import logging
import yaml
from typing import Union, Any, List, Dict, Tuple, Optional, cast, Iterator
from abc import ABC
import subprocess

import jinja2

logger: logging.Logger = logging.getLogger(__name__)


class Subscriptable(ABC):
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


class UserError(Exception):
    pass


def realpath(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))


def run_command(command: str, cwd: str, return_stdout: bool = False) -> str:
    result = subprocess.run(command,
                            shell=True,
                            check=True,
                            cwd=cwd,
                            capture_output=True)

    if return_stdout:
        return result.stdout.decode()

    if result.stdout:
        logger.info(result.stdout)

    return ''


def render_template(
    contents: str,
    variables: Dict[str, Any],
    directory: str = None,
) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(directory)) \
        if directory is not None else jinja2.Environment()
    template = env.from_string(contents)
    rendered = template.render(variables)
    return rendered


def saved_sys_properties() -> Iterator[None]:
    """Save various sys properties such as sys.path and sys.modules."""
    old_path = sys.path.copy()
    old_modules = sys.modules.copy()

    try:
        yield
    finally:
        sys.path = old_path
        for module in set(sys.modules).difference(old_modules):
            del sys.modules[module]


def read_header(path: str) -> Dict[Any, Any]:
    header_lines = []
    with open(path, 'r') as f:
        for line in f:
            if line == '#\n':
                header_lines.append('\n')
            if line.startswith('# '):
                header_lines.append(line[2:])
            else:
                break
    header = yaml.safe_load(''.join(header_lines))
    if not header:
        header = {}
    if not isinstance(header, dict):
        raise UserError(f"invalid YAML header for {path}")
    return header
