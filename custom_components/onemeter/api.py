import logging
import os

import requests
import urllib3
from bs4 import BeautifulSoup

from const import DOMAIN, HOST

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOGLEVEL', 'INFO').upper()
)



urllib3.disable_warnings()


class OnemeterApi:
    def __init__(self, apikey, device_uuid) -> None:
        self.apikey = apikey
        self.device_uuid = device_uuid
        self.base_url = "https://" + HOST + "/api/"
        self.headers = {
            "Authorization": self.apikey
        }
    
    def get_user(self) -> dict:
        url = self.base_url + "user"
        response = requests.get(url, headers=self.headers)
        _LOGGER.debug(f"{DOMAIN} - user response {response.text}")
        return response

    def get_device(self) -> dict:
        url = self.base_url + "devices/" + self.device_uuid
        response = requests.get(url, headers=self.headers)
        _LOGGER.debug(f"{DOMAIN} - device response {response.text}")
        return response
    
    def get_data(self) -> dict:
        url = self.base_url + "devices/" + self.device_uuid
        response = requests.get(url, headers=self.headers)
        _LOGGER.debug(f"{DOMAIN} - data response {response.text}")
        
        json = response.json()
        energy_code = json["config"]["usageKeys"]["activeEnergy"]
        last_energy = json["lastReading"]["OBIS"].get(energy_code)
        last_energy_negative = json["lastReading"]["OBIS"].get("2_8_0")

        return { last_energy, last_energy_negative}
