from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field, fields
from abc import ABC
from typing import Dict, List, Any, TypeVar, Type, Optional, Iterable, Tuple, cast
import yaml

from powar.util import Subscriptable, UserError, run_command, render_template

logger: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseConfig")
@dataclass
class BaseConfig(Subscriptable, ABC):

    @classmethod
    def from_yaml_path(cls: Type[T], *path_elements: str) -> T:
        path = os.path.join(*path_elements)

        with open(path, "r") as stream:
            config_raw = yaml.load(stream, Loader=yaml.SafeLoader)

        unrecognised = set(config_raw) - set(f.name for f in fields(cls))
        if unrecognised:
            raise UserError(*(f"field \"{k}\" unrecognised in {path}"
                              for k in unrecognised))

        return cls(**config_raw) # type: ignore


@dataclass
class ModuleConfig(BaseConfig):
    install: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    system_packages: List[str] = field(default_factory=list)
    depends: List[str] = field(default_factory=list)
    exec_before: Optional[str] = None
    exec_after: Optional[str] = None


@dataclass
class GlobalConfig(BaseConfig):
    modules: List[str]
    variables: Dict[str, Any]


def execute_command_fields(cwd: str, variables: Dict[str, Any], value: Any) -> None:
    it: Iterable[Tuple[Any, Any]]
    if isinstance(value, dict):
        it = value.items()
    elif isinstance(value, list):
        it = enumerate(value)
    else:
        return

    for k, v in it:
        if isinstance(v, str):
            v = v.strip("\n")

            if not v.endswith("`"):
                continue

            mode: str
            substr: slice
            if v.startswith("`"):
                mode = "exec"
                substr = slice(1,-1)
            elif v.startswith("parse`"):
                mode = "parse"
                substr = slice(6,-1)
            else:
                continue

            contents = render_template(contents=v[substr], variables=variables)
            assert isinstance(contents, str)

            if mode == "parse":
                value[k] = yaml.load(run_command(contents, cwd, return_stdout=True), Loader=yaml.SafeLoader)
            elif mode == "exec":
                value[k] = run_command(contents, cwd, return_stdout=True)
            else:
                assert False

            logger.info(f"Executed command in config {v}")
        else:
            execute_command_fields(value=v, variables=variables, cwd=cwd)
