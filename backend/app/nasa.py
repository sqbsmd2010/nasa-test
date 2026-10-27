"""NASA API proxy. The API key lives only here, never in the browser."""
import os
from datetime import date, timedelta

import httpx
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
_cache: TTLCache = TTLCache(maxsize=256, ttl=900)  # 15 min: saves rate limit, survives outages


async def get(path: str, **params):
    k = (path, tuple(sorted(params.items())))
    if k in _cache:
        return _cache[k]
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://api.nasa.gov{path}", params={**params, "api_key": KEY})
        r.raise_for_status()
    _cache[k] = r.json()
    return _cache[k]


async def solar_flares(days: int = 7):
    end = date.today()
    return await get("/DONKI/FLR", startDate=str(end - timedelta(days=days)), endDate=str(end))


async def apod():
    return await get("/planetary/apod")


async def epic_latest():
    return await get("/EPIC/api/natural")
