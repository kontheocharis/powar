import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from logging import CRITICAL, WARNING, INFO

from powar.util import Subscriptable


class AppMode(Enum):
    INSTALL = 0
    LIST_PACKAGES = 1
    NEW_MODULE = 2
    INIT = 3


class AppLogLevel(Enum):
    NORMAL = 0
    VERBOSE = 1
    QUIET = 2

    def into_logging_level(self) -> int:
        if self == AppLogLevel.NORMAL:
            return WARNING
        if self == AppLogLevel.VERBOSE:
            return INFO
        if self == AppLogLevel.QUIET:
            return CRITICAL
        assert False


@dataclass
class AppSettings(Subscriptable):
    data_path: str = os.path.join(os.path.dirname(__file__), "../data")
    module_config_template_filename: str = "module-template.py"
    global_config_template_filename: str = "global-template.py"

    template_dir: str = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"), "powar-templates")

    config_dir: str = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"), "powar-config")

    cache_dir: str = os.path.join(
        os.environ.get("XDG_DATA_HOME", "$HOME/.local/share"), "powar")

    module_config_filename: str = "powar.py"
    global_config_filename: str = "global.py"
    modules_to_consider: List[str] = field(default_factory=list)

    log_level: AppLogLevel = AppLogLevel.NORMAL

    dry_run: bool = False

    mode: Optional[AppMode] = None

    new_module_name: Optional[str] = None

    init: bool = False

    switch_to_root: bool = False
