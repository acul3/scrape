import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError
import asyncio
import json
from json.decoder import JSONDecodeError
from pathlib import Path


class Liputan6:
    headers = {
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0',
        'accept': 'text/html,application/xhtml+xml,application/xml',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,id;q=0.8,de;q=0.7,ms;q=0.67'
    }
    categories = {
        "news": "https://www.liputan6.com/{category}/indeks/{date}",
        "bisnis": "https://www.liputan6.com/{category}/indeks/{date}",
        "saham": "https://www.liputan6.com/{category}/indeks/{date}",
        "showbiz": "https://www.liputan6.com/{category}/indeks/{date}",
        "crypto": "https://www.liputan6.com/{category}/indeks/{date}",
        "tekno": "https://www.liputan6.com/{category}/indeks/{date}",
        "otomotif": "https://www.liputan6.com/{category}/indeks/{date}",
        "global": "https://www.liputan6.com/{category}/indeks/{date}",
        "lifestyle": "https://www.liputan6.com/{category}/indeks/{date}",
        "health": "https://www.liputan6.com/{category}/indeks/{date}",
        "bola": "https://www.liputan6.com/{category}/indeks/{date}",
    }
    liputan_wait = Path("/tmp/liputan_wait.txt")

    def __init__(self):
        pass