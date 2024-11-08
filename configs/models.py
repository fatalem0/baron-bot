import argparse
import json
import pathlib
import dataclasses
import enum


@dataclasses.dataclass
class JobConfig:
    interval: int
    first:int

@dataclasses.dataclass
class JobsConfig:
    approve_event_if_has_min_attendees: JobConfig

@dataclasses.dataclass
class Config:
    telegram_token: str
    gis_token: str
    sslrootcert: str
    schema:str
    jobs: JobsConfig


class Environment(str, enum.Enum):
    local = 'local'
    production = 'production'


def load_config(env: Environment) -> Config:
    config_path = pathlib.Path(__file__).parent / f'config.{env.value}.json'
    with config_path.open() as config:
        config_json = json.load(config)
        return Config(
            telegram_token=config_json['telegram']['token'],
            gis_token=config_json['2gis']['token'],
            sslrootcert=config_json['db']['sslrootcert'],
            schema=config_json['db']['schema'],
            jobs=config_json['jobs']
        )

def load_config_global() -> Config:
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=Environment, required=False, default=Environment.local)
    args = parser.parse_args()
    return load_config(args.env)