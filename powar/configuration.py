from __future__ import annotations

import os
import yaml

from abc import ABC
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class BaseConfig(ABC):

    @classmethod
    def from_yaml_path(cls, *path_elements: List[str]) -> YamlConfig:
        path = os.path.join(*path_elements)

        with open(os.path.join(path), 'r') as stream:
            config_raw = yaml.load(stream, Loader=yaml.SafeLoader)

        return cls(**config_raw)

@dataclass
class ModuleConfig(BaseConfig):
    install: Dict[str,str]
    variables: Dict[str, Any]
    system_packages: List[str]
    run_before: str
    run_after: str

@dataclass
class GlobalConfig(BaseConfig):
    modules: List[str]
    variables: Dict[str, Any]
