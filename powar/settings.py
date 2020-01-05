import os

from dataclasses import dataclass, field

@dataclass
class AppSettings:

    template_dir: str = field(
        default=os.path.join(os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"), "powar-templates")
    )

    config_dir: str = field(
        default=os.path.join(os.environ.get("XDG_CONFIG_HOME", "$HOME/.config"), "powar-config")
    )

    cache_dir: str = field(
        default=os.path.join(os.environ.get("XDG_DATA_HOME", "$HOME/.local/share"), "powar")
    )

    module_config_filename: str = field(default="powar.yml")

    global_config_filename: str = field(default='global.yml')

    dry_run: bool = field(default=False)

    first_run: bool = field(default=False)

    execute: bool = field(default=True)
