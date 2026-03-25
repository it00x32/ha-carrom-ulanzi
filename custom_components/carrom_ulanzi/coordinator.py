"""DataUpdateCoordinator for Carrom Ulanzi Display."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CarromUlanziCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls Carrom live data from Firebase RTDB."""

    def __init__(
        self, hass: HomeAssistant, url: str, scan_interval: int
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(self._url, timeout=10) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status} from {self._url}")
                data = await resp.json(content_type=None)
                if not isinstance(data, dict):
                    raise UpdateFailed("Response is not a JSON object")
                return data
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Carrom fetch failed: {err}") from err
