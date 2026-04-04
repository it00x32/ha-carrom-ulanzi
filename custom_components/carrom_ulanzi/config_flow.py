"""Config flow for Carrom Ulanzi Display."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_APP_NAME,
    CONF_DURATION,
    CONF_ICON,
    CONF_PAUSE_TEXT,
    CONF_LAST_PLAYER_COLOR,
    CONF_LEADER_COLOR,
    CONF_MQTT_PREFIX,
    CONF_RAINBOW,
    CONF_ROUND_COLOR,
    CONF_SCAN_INTERVAL,
    CONF_SCROLL_SPEED,
    CONF_TEXT_COLOR,
    CONF_URL,
    DEFAULT_APP_NAME,
    DEFAULT_DURATION,
    DEFAULT_ICON,
    DEFAULT_PAUSE_TEXT,
    DEFAULT_LAST_PLAYER_COLOR,
    DEFAULT_LEADER_COLOR,
    DEFAULT_MQTT_PREFIX,
    DEFAULT_RAINBOW,
    DEFAULT_ROUND_COLOR,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCROLL_SPEED,
    DEFAULT_TEXT_COLOR,
    DEFAULT_URL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CarromUlanziConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip()
            prefix = user_input[CONF_MQTT_PREFIX].strip()

            session = async_get_clientsession(self.hass)
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        data = await resp.json(content_type=None)
                        if not isinstance(data, dict) or "scores" not in data:
                            errors["base"] = "invalid_data"
            except Exception:
                _LOGGER.exception("Error connecting to %s", url)
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(f"{url}_{prefix}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Carrom → {prefix}",
                    data={
                        CONF_URL: url,
                        CONF_MQTT_PREFIX: prefix,
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=DEFAULT_URL): TextSelector(),
                vol.Required(
                    CONF_MQTT_PREFIX, default=DEFAULT_MQTT_PREFIX
                ): TextSelector(),
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return CarromUlanziOptionsFlow()


class CarromUlanziOptionsFlow(config_entries.OptionsFlow):
    """Options flow — all settings including URL and display tuning."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_URL, default=opts.get(CONF_URL, DEFAULT_URL)
                ): TextSelector(),
                vol.Required(
                    CONF_MQTT_PREFIX,
                    default=opts.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX),
                ): TextSelector(),
                vol.Required(
                    CONF_APP_NAME,
                    default=opts.get(CONF_APP_NAME, DEFAULT_APP_NAME),
                ): TextSelector(),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_SCROLL_SPEED,
                    default=opts.get(CONF_SCROLL_SPEED, DEFAULT_SCROLL_SPEED),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=10, max=500, step=10, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Required(
                    CONF_DURATION,
                    default=opts.get(CONF_DURATION, DEFAULT_DURATION),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=120,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_TEXT_COLOR,
                    default=opts.get(CONF_TEXT_COLOR, DEFAULT_TEXT_COLOR),
                ): TextSelector(),
                vol.Required(
                    CONF_LEADER_COLOR,
                    default=opts.get(CONF_LEADER_COLOR, DEFAULT_LEADER_COLOR),
                ): TextSelector(),
                vol.Required(
                    CONF_LAST_PLAYER_COLOR,
                    default=opts.get(
                        CONF_LAST_PLAYER_COLOR, DEFAULT_LAST_PLAYER_COLOR
                    ),
                ): TextSelector(),
                vol.Required(
                    CONF_ROUND_COLOR,
                    default=opts.get(CONF_ROUND_COLOR, DEFAULT_ROUND_COLOR),
                ): TextSelector(),
                vol.Required(
                    CONF_RAINBOW,
                    default=opts.get(CONF_RAINBOW, DEFAULT_RAINBOW),
                ): BooleanSelector(),
                vol.Optional(
                    CONF_ICON, default=opts.get(CONF_ICON, DEFAULT_ICON)
                ): TextSelector(),
                vol.Required(
                    CONF_PAUSE_TEXT,
                    default=opts.get(CONF_PAUSE_TEXT, DEFAULT_PAUSE_TEXT),
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
