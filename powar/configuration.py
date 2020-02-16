from __future__ import annotations

import os
import yaml
import dataclasses
from dataclasses import dataclass, field

from abc import ABC
from typing import Dict, List, Any, TypeVar, Type

from powar.util import Subscriptable, UserError

T = TypeVar("T")
@dataclass
class BaseConfig(Subscriptable, ABC):

    @classmethod
    def from_yaml_path(cls: Type[T], *path_elements: List[str]) -> T:
        path = os.path.join(*path_elements)

        with open(path, "r") as stream:
            config_raw = yaml.load(stream, Loader=yaml.SafeLoader)

        for k in config_raw:
            if k not in (f.name for f in dataclasses.fields(cls)):
                raise UserError(f"field \"{k}\" unrecognised in {path}")

        return cls(**config_raw)


@dataclass
class ModuleConfig(BaseConfig):
    install: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    system_packages: List[str] = field(default_factory=list)
    depends: List[str] = field(default_factory=list)
    exec_before: str = None
    exec_after: str = None

@dataclass
class GlobalConfig(BaseConfig):
    modules: List[str]
    variables: Dict[str, Any]
