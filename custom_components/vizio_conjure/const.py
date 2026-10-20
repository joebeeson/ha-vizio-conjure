from __future__ import annotations

DOMAIN = "vizio_conjure"

CONF_HOST = "host"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NAME = "device_name"
CONF_AUTH_TOKEN = "auth_token"
CONF_PROFILE_NAME = "profile_name"

SERVICE_LAUNCH = "launch"
SERVICE_SHOW_LOVELACE_VIEW = "show_lovelace_view"
SERVICE_RELOAD = "reload"
SERVICE_EXIT = "exit"
SERVICE_SEND_KEY = "send_key"
ATTR_URL = "url"
ATTR_ENTRY_ID = "entry_id"
ATTR_TARGET = "target"
ATTR_TARGET_NAME = "target_name"
ATTR_DASHBOARD_PATH = "dashboard_path"
ATTR_VIEW_PATH = "view_path"
ATTR_KEY = "key"

CONF_TARGETS = "targets"

PLATFORMS = ("sensor",)

BRIDGE_EVENT = "vizio_conjure_page_event"
BRIDGE_PATH = "/api/vizio_conjure/bridge"
BRIDGE_TTL_SECONDS = 300

ALLOWED_KEYS = frozenset(
    {
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT",
        "OK",
        "BACK",
        "EXIT",
        "HOME",
        "MENU",
        "PLAY",
        "PAUSE",
    }
)

PAGE_SUBJECTS = frozenset({"page.ready", "page.error", "page.focus", "page.interaction"})
COMMAND_SUBJECTS = frozenset({"page.navigate", "page.reload", "page.focus", "session.close"})

DEFAULT_DEVICE_NAME = "ha-vizio-conjure"
