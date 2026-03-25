"""Constants for Carrom Ulanzi Display."""

DOMAIN = "carrom_ulanzi"

CONF_URL = "url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MQTT_PREFIX = "mqtt_prefix"
CONF_APP_NAME = "app_name"
CONF_SCROLL_SPEED = "scroll_speed"
CONF_TEXT_COLOR = "text_color"
CONF_LEADER_COLOR = "leader_color"
CONF_ROUND_COLOR = "round_color"
CONF_RAINBOW = "rainbow"
CONF_DURATION = "duration"
CONF_ICON = "icon"

DEFAULT_URL = (
    "https://carrom-scorekeeper-default-rtdb.europe-west1.firebasedatabase.app"
    "/live_api.json"
)
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_MQTT_PREFIX = "awtrix"
DEFAULT_APP_NAME = "carrom"
DEFAULT_SCROLL_SPEED = 100
DEFAULT_TEXT_COLOR = "FFFFFF"
DEFAULT_LEADER_COLOR = "00FF00"
DEFAULT_ROUND_COLOR = "FFAA00"
DEFAULT_RAINBOW = False
DEFAULT_DURATION = 15
DEFAULT_ICON = ""
DEFAULT_LIFETIME = 120

MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 3600
