from typing import Optional

import requests
import dataclasses

from configs.models import Config


@dataclasses.dataclass
class BuildingItem:
    address_comment: Optional[str]
    address_name: str
    id: str
    name: str


class GisAPI:
    BASE_URL = 'https://catalog.api.2gis.com/3.0'

    def __init__(self, config: Config):
        self.key = config.gis_token

    def __get__(self, lat: float, lon: float, prompt: str):
        response = requests.get(
            url=f'{self.BASE_URL}/items',
            params={
                'key': self.key,
                'q': prompt,
                'sort_point': f'{lat},{lon}',
            },
            verify=False,
        )

        response.raise_for_status()
        print(response.json())
        assert response.json()['meta']['code'] == 200
        return response.json()['result']['items']

    def adv(self, lat: float, lon: float, prompt: str = 'Бар') -> list[BuildingItem]:
        items = self.__get__(lat=lat, lon=lon, prompt=prompt)
        return [
            BuildingItem(
                address_comment=item.get('address_comment'),
                address_name=item['address_name'],
                id=item['id'],
                name=item['name'],
            ) for item in items
        ]
