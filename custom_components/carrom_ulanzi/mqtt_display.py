"""Awtrix MQTT display publisher for Carrom scores."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.mqtt import async_publish
from homeassistant.core import HomeAssistant

from .const import (
    CONF_APP_NAME,
    CONF_DURATION,
    CONF_ICON,
    CONF_LAST_PLAYER_COLOR,
    CONF_LEADER_COLOR,
    CONF_RAINBOW,
    CONF_ROUND_COLOR,
    CONF_SCROLL_SPEED,
    CONF_PAUSE_TEXT,
    CONF_TEXT_COLOR,
    DEFAULT_APP_NAME,
    DEFAULT_DURATION,
    DEFAULT_ICON,
    DEFAULT_LAST_PLAYER_COLOR,
    DEFAULT_LEADER_COLOR,
    DEFAULT_LIFETIME,
    DEFAULT_RAINBOW,
    DEFAULT_ROUND_COLOR,
    DEFAULT_PAUSE_TEXT,
    DEFAULT_SCROLL_SPEED,
    DEFAULT_TEXT_COLOR,
)

_LOGGER = logging.getLogger(__name__)


class AwtrixDisplay:
    """Formats Carrom scores and publishes them to an Awtrix device via MQTT."""

    def __init__(self, hass: HomeAssistant, prefix: str) -> None:
        self._hass = hass
        self._prefix = prefix
        self._app_name = DEFAULT_APP_NAME
        self._last_game_id: str | None = None
        self._winner_notified = False
        self._last_round = 0

    def _opt(self, options: dict, key: str, default: Any) -> Any:
        return options.get(key, default)

    async def async_update(
        self, data: dict[str, Any] | None, options: dict[str, Any]
    ) -> None:
        """Format scores and publish to Awtrix custom app topic."""
        if not data:
            return

        self._app_name = self._opt(options, CONF_APP_NAME, DEFAULT_APP_NAME)
        topic = f"{self._prefix}/custom/{self._app_name}"

        game_id = data.get("game_id")
        if game_id != self._last_game_id:
            self._last_game_id = game_id
            self._winner_notified = False
            self._last_round = 0

        is_paused = data.get("is_paused", False)
        if is_paused:
            pause_payload = self._build_pause_payload(options)
            await async_publish(self._hass, topic, json.dumps(pause_payload))
            return

        names = data.get("names", [])
        scores = data.get("scores", [])
        rounds_played = data.get("rounds_played", 0)
        target = data.get("target", "0")

        payload = self._build_payload(names, scores, rounds_played, options)
        await async_publish(self._hass, topic, json.dumps(payload))

        await self._check_events(names, scores, rounds_played, target, options)

    def _build_pause_payload(self, options: dict[str, Any]) -> dict[str, Any]:
        """Show configurable text while the Carrom game is paused."""
        scroll_speed = int(self._opt(options, CONF_SCROLL_SPEED, DEFAULT_SCROLL_SPEED))
        duration = int(self._opt(options, CONF_DURATION, DEFAULT_DURATION))
        round_color = self._opt(options, CONF_ROUND_COLOR, DEFAULT_ROUND_COLOR)
        rainbow = self._opt(options, CONF_RAINBOW, DEFAULT_RAINBOW)
        icon = self._opt(options, CONF_ICON, DEFAULT_ICON)
        raw = self._opt(options, CONF_PAUSE_TEXT, DEFAULT_PAUSE_TEXT)
        pause_text = (raw if isinstance(raw, str) else str(raw)).strip() or DEFAULT_PAUSE_TEXT

        if rainbow:
            payload: dict[str, Any] = {
                "text": pause_text,
                "rainbow": True,
            }
        else:
            payload = {
                "text": [{"t": pause_text, "c": round_color}],
            }

        payload["scrollSpeed"] = scroll_speed
        payload["duration"] = duration
        payload["lifetime"] = DEFAULT_LIFETIME
        payload["pushIcon"] = 2
        if icon:
            payload["icon"] = icon
        return payload

    def _build_payload(
        self,
        names: list[str],
        scores: list[int],
        rounds_played: int,
        options: dict[str, Any],
    ) -> dict[str, Any]:
        rainbow = self._opt(options, CONF_RAINBOW, DEFAULT_RAINBOW)
        scroll_speed = int(self._opt(options, CONF_SCROLL_SPEED, DEFAULT_SCROLL_SPEED))
        duration = int(self._opt(options, CONF_DURATION, DEFAULT_DURATION))
        icon = self._opt(options, CONF_ICON, DEFAULT_ICON)

        if rainbow:
            plain = self._plain_text(names, scores, rounds_played)
            payload: dict[str, Any] = {
                "text": plain,
                "rainbow": True,
            }
        else:
            payload = {"text": self._colored_fragments(names, scores, rounds_played, options)}

        payload["scrollSpeed"] = scroll_speed
        payload["duration"] = duration
        payload["lifetime"] = DEFAULT_LIFETIME
        payload["pushIcon"] = 2

        if icon:
            payload["icon"] = icon

        return payload

    def _plain_text(
        self, names: list[str], scores: list[int], rounds_played: int
    ) -> str:
        parts = []
        for i, (name, score) in enumerate(zip(names, scores)):
            sep = " | " if i > 0 else ""
            parts.append(f"{sep}{name}: {score}")
        parts.append(f"  (Runde {rounds_played})")
        return "".join(parts)

    def _colored_fragments(
        self,
        names: list[str],
        scores: list[int],
        rounds_played: int,
        options: dict[str, Any],
    ) -> list[dict[str, str]]:
        text_color = self._opt(options, CONF_TEXT_COLOR, DEFAULT_TEXT_COLOR)
        leader_color = self._opt(options, CONF_LEADER_COLOR, DEFAULT_LEADER_COLOR)
        last_player_color = self._opt(
            options, CONF_LAST_PLAYER_COLOR, DEFAULT_LAST_PLAYER_COLOR
        )
        round_color = self._opt(options, CONF_ROUND_COLOR, DEFAULT_ROUND_COLOR)

        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        leader_idx = {i for i, s in enumerate(scores) if s == max_score}
        if max_score != min_score:
            trailer_idx = {i for i, s in enumerate(scores) if s == min_score}
        else:
            trailer_idx = set()

        fragments: list[dict[str, str]] = []
        for i, (name, score) in enumerate(zip(names, scores)):
            if i > 0:
                fragments.append({"t": " | ", "c": text_color})
            if i in leader_idx:
                color = leader_color
            elif i in trailer_idx:
                color = last_player_color
            else:
                color = text_color
            fragments.append({"t": f"{name}: {score}", "c": color})

        fragments.append({"t": f"  (Runde {rounds_played})", "c": round_color})
        return fragments

    async def _check_events(
        self,
        names: list[str],
        scores: list[int],
        rounds_played: int,
        target: str,
        options: dict[str, Any],
    ) -> None:
        try:
            target_val = int(target)
        except (ValueError, TypeError):
            return

        if not self._winner_notified:
            for i, score in enumerate(scores):
                if score >= target_val and i < len(names):
                    leader_color = self._opt(
                        options, CONF_LEADER_COLOR, DEFAULT_LEADER_COLOR
                    )
                    icon = self._opt(options, CONF_ICON, DEFAULT_ICON)
                    notify = {
                        "text": f"{names[i]} gewinnt mit {score} Punkten!",
                        "color": leader_color,
                        "duration": 10,
                    }
                    if icon:
                        notify["icon"] = icon
                    await async_publish(
                        self._hass,
                        f"{self._prefix}/notify",
                        json.dumps(notify),
                    )
                    self._winner_notified = True
                    _LOGGER.info("Carrom winner notification sent for %s", names[i])
                    break

        if rounds_played > self._last_round and self._last_round > 0:
            _LOGGER.debug(
                "Carrom round change: %d -> %d", self._last_round, rounds_played
            )
        self._last_round = rounds_played

    async def async_remove(self) -> None:
        """Remove the custom app from Awtrix by sending empty payload."""
        try:
            await async_publish(
                self._hass, f"{self._prefix}/custom/{self._app_name}", ""
            )
        except Exception:
            _LOGGER.debug("Could not remove Awtrix app on unload")
