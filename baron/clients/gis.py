import requests

from configs.models import Config


class GisAPI:
    BASE_URL = 'https://catalog.api.2gis.com/3.0'

    def __init__(self, config: Config):
        self.key = config.gis_token
        self.prompt = "Бар"
        pass

    def __get__(self, lat: float, lon: float):
        response = requests.get(
            url=f'{self.BASE_URL}/items',
            params={
                'key': self.key,
                'q': self.prompt,
                'sort_point': [lat, lon],
            },
            verify=False,
        )
        response.raise_for_status()
        return response.json()
