import os
from dataclasses import dataclass, field
from typing import List, Literal
from enum import Enum
from logging import CRITICAL, WARNING, INFO

from powar.util import Subscriptable


class AppMode(Enum):
    INSTALL = 0
    UPDATE = 1
    LIST_PACKAGES = 2

class AppLogLevel(Enum):
    NORMAL = 0
    VERBOSE = 1
    QUIET = 2

    def into_logging_level(self) -> int:
        if self == AppLogLevel.NORMAL:
            return WARNING
        elif self == AppLogLevel.VERBOSE:
            return INFO
        elif self == AppLogLevel.QUIET:
            return CRITICAL

@dataclass
class AppSettings(Subscriptable):
    template_dir: str = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"),
        "powar-templates")

    config_dir: str = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"),
        "powar-config")

    cache_dir: str = os.path.join(
        os.environ.get("XDG_DATA_HOME", "$HOME/.local/share"),
        "powar")

    module_config_filename: str = "powar.yml"
    global_config_filename: str = "global.yml"
    modules_to_consider: List[str] = field(default_factory=list)

    log_level: AppLogLevel = AppLogLevel.NORMAL

    dry_run: bool = False
    execute: bool = True

    mode: AppMode = None
