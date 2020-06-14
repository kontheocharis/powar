import os
import logging
from typing import Union, Any, List, Dict, Tuple, Optional, cast
from abc import ABC
import subprocess

import jinja2
from powar.jinja_ext import ExternalExtension

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


def run_command(command: str,
                cwd: str,
                return_stdout: bool = False
                ) -> Optional[str]:
    result = subprocess.run(command, shell=True, check=True, cwd=cwd, capture_output=True)

    if return_stdout:
        return result.stdout.decode()

    if result.stdout:
        logger.info(result.stdout)

    return None


def render_template(contents: str,
                    variables: Dict[str, Any],
                    directory: str = None,
                    external_installs: bool = False
                    ) -> Union[str, Tuple[str, List[Tuple[str, str]]]]:
    class EnvironmentWithExternalInstalls(jinja2.Environment):
        external_installs: List[Tuple[str, str]]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(directory)) \
        if directory is not None else jinja2.Environment()

    if external_installs:
        env.add_extension(ExternalExtension)

    template = env.from_string(contents)

    rendered = template.render(variables)

    if external_installs:
        return rendered, cast(EnvironmentWithExternalInstalls, env).external_installs

    return rendered
