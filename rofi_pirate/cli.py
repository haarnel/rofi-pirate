from rofi_pirate.config import Config
from rofi_pirate.rofi import Rofi


def cli():
    config = Config()
    config.load_config()
    Rofi(config).run()