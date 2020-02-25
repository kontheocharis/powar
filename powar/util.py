import os
from typing import Union, Any, List, Dict, Tuple

from abc import ABC
import jinja2
import subprocess
from powar.jinja_ext import ExternalExtension


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


def run_command(command: str, cwd: str, return_stdout: bool=False) -> Union[str, None]:
    result = subprocess.run(command, shell=True, check=True, cwd=cwd, capture_output=True)

    if return_stdout:
        return result.stdout

    if result.stdout:
        logger.info(result.stdout)


def render_template(
        contents: str,
        variables: Dict[str, Any],
        directory: str=None,
        external_installs=False) -> Union[str, Tuple[str, List[Tuple[str, str]]]]:

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(directory)) \
        if directory is not None else jinja2.Environment()

    if external_installs:
        env.add_extension(ExternalExtension)

    template = env.from_string(contents)

    rendered = template.render(variables)

    if external_installs:
        return rendered, env.external_installs

    return rendered
