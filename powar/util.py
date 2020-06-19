import os
import sys
import logging
import contextlib
import yaml
from typing import Union, Any, List, Dict, Tuple, Optional, cast, Iterator, Iterable
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


def run_command(
    command: str,
    cwd: str,
    stdin: Optional[bytes] = None,
    decode_stdout=True,
    wait=True,
) -> Optional[Union[str, bytes]]:
    popenargs = {
        'args': command,
        'shell': True,
        'stdin': subprocess.PIPE,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'cwd': cwd,
    }

    process = subprocess.Popen(**popenargs)
    if not wait:
        return
    try:
        stdout, stderr = process.communicate(stdin)
    except:
        process.kill()
        raise
    retcode = process.poll()
    if retcode:
        try:
            print(stderr.decode())
        except UnicodeDecodeError:
            print(stderr)
        raise subprocess.CalledProcessError(
            retcode,
            process.args,
            output=stdout,
            stderr=stderr,
        )

    if decode_stdout:
        return stdout.decode()
    else:
        return stdout


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


@contextlib.contextmanager
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
