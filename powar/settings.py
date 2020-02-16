import os
from dataclasses import dataclass

from powar.util import Subscriptable


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
    dry_run: bool = False
    first_run: bool = False
    execute: bool = True
    list_packages: bool = False
