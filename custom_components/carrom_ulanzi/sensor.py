"""Diagnostic sensors for Carrom Ulanzi Display."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX, DOMAIN
from .coordinator import CarromUlanziCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CarromUlanziCoordinator = hass.data[DOMAIN][entry.entry_id][0]
    prefix = entry.options.get(
        CONF_MQTT_PREFIX, entry.data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
    )
    async_add_entities(
        [
            CarromUlanziStatusSensor(coordinator, entry.entry_id, prefix),
            CarromUlanziLastUpdateSensor(coordinator, entry.entry_id, prefix),
        ]
    )


def _device_info(entry_id: str, prefix: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=f"Carrom Ulanzi ({prefix})",
        manufacturer="Carrom App",
        model="Awtrix MQTT Display",
    )


class CarromUlanziStatusSensor(
    CoordinatorEntity[CarromUlanziCoordinator], SensorEntity
):
    """Shows OK / Paused / Error based on coordinator state."""

    _attr_icon = "mdi:monitor-dashboard"
    _attr_translation_key = "display_status"

    def __init__(
        self,
        coordinator: CarromUlanziCoordinator,
        entry_id: str,
        prefix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"carrom_ulanzi_{entry_id}_status"
        self._attr_device_info = _device_info(entry_id, prefix)

    @property
    def name(self) -> str:
        return "Carrom Display Status"

    @property
    def native_value(self) -> str:
        if self.coordinator.last_update_success is False:
            return "Fehler"
        data = self.coordinator.data
        if not data:
            return "Warte auf Daten"
        if data.get("is_paused", False):
            return "Pausiert"
        return "OK"

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            "game_id": data.get("game_id"),
            "rounds_played": data.get("rounds_played"),
            "target": data.get("target"),
            "mode": data.get("mode"),
            "source_url": self.coordinator.url,
        }


class CarromUlanziLastUpdateSensor(
    CoordinatorEntity[CarromUlanziCoordinator], SensorEntity
):
    """Timestamp of the last successful data update from Firebase."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"
    _attr_translation_key = "last_update"

    def __init__(
        self,
        coordinator: CarromUlanziCoordinator,
        entry_id: str,
        prefix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"carrom_ulanzi_{entry_id}_last_update"
        self._attr_device_info = _device_info(entry_id, prefix)

    @property
    def name(self) -> str:
        return "Carrom Letztes Update"

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data or {}
        ts = data.get("last_update")
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            return None
