import json
import pathlib
import dataclasses
import enum


@dataclasses.dataclass
class Config:
    telegram_token: str
    gis_token: str


class Environment(str, enum.Enum):
    local = 'local'
    production = 'production'


def load_config(env: Environment) -> Config:
    config_path = pathlib.Path(__file__).parent / f'config.{env}.json'
    with config_path.open() as config:
        config_json = json.load(config)
        return Config(
            telegram_token=config_json['telegram']['token'],
            gis_token=config_json['2gis']['token'],
        )
