"""Constants for the Siegenia integration."""

DOMAIN = "siegenia"

# Configuration constants
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_USE_SSL = "use_ssl"

# Default values
DEFAULT_PORT = 443
DEFAULT_USERNAME = "admin"
DEFAULT_USE_SSL = True

# Device types from ioBroker adapter
DEVICE_TYPE_MAP = {
    1: "AEROPAC",
    2: "AEROMAT VT", 
    3: "DRIVE axxent Family",
    4: "SENSOAIR",
    5: "AEROVITAL",
    6: "MHS Family",
    7: "reserved",
    8: "AEROTUBE",
    9: "GENIUS B",
    10: "Universal Module"
}

# AEROPAC specific constants
AEROPAC_FAN_LEVELS = {
    0: "Off",
    1: "Level 1",
    2: "Level 2", 
    3: "Level 3",
    4: "Level 4",
    5: "Level 5",
    6: "Level 6",
    7: "Level 7"
}

# WebSocket timeouts
WS_TIMEOUT = 10
WS_HEARTBEAT_INTERVAL = 30