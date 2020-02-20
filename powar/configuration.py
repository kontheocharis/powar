from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from abc import ABC
from typing import Dict, List, Any, TypeVar, Type
import yaml

from powar.util import Subscriptable, UserError


T = TypeVar("T")
@dataclass
class BaseConfig(Subscriptable, ABC):

    @classmethod
    def from_yaml_path(cls: Type[T], *path_elements: List[str]) -> T:
        path = os.path.join(*path_elements)

        with open(path, "r") as stream:
            config_raw = yaml.load(stream, Loader=yaml.SafeLoader)

        unrecognised = set(config_raw) - set(f.name for f in fields(cls))
        if unrecognised:
            raise UserError(*(f"field \"{k}\" unrecognised in {path}"
                              for k in unrecognised))

        return cls(**config_raw)

@dataclass
class GlobalConfig(BaseConfig):
    modules: List[str]
    variables: Dict[str, Any]
