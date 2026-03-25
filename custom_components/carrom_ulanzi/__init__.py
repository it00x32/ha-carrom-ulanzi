"""Carrom Ulanzi Display — Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MQTT_PREFIX,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import CarromUlanziCoordinator
from .mqtt_display import AwtrixDisplay

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

type CarromUlanziData = tuple[CarromUlanziCoordinator, AwtrixDisplay]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Carrom Ulanzi Display from a config entry."""
    opts = {**entry.data, **entry.options}

    url = opts[CONF_URL]
    prefix = opts.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
    scan_interval = int(opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    coordinator = CarromUlanziCoordinator(hass, url, scan_interval)
    display = AwtrixDisplay(hass, prefix)

    async def _on_update() -> None:
        """Push scores to Awtrix whenever coordinator refreshes."""
        if coordinator.data is not None:
            await display.async_update(coordinator.data, opts)

    coordinator.async_add_listener(_on_update)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (coordinator, display)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload: remove Awtrix app and clean up."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coordinator, display = hass.data[DOMAIN].pop(entry.entry_id)
        await display.async_remove()
    return ok
