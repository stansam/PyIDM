"""Application-wide constants and default configuration values."""

from typing import Final

# Network Defaults
DEFAULT_USER_AGENT: Final[str] = "PyIDM/1.0 (+https://github.com/pyidm/pyidm)"
DEFAULT_CHUNK_SIZE_BYTES: Final[int] = 65536  # 64 KB
MIN_SEGMENT_SIZE_BYTES: Final[int] = 1048576  # 1 MB
DEFAULT_CONNECTIONS_PER_DOWNLOAD: Final[int] = 4
MAX_CONNECTIONS_PER_DOWNLOAD: Final[int] = 32
DEFAULT_CONNECT_TIMEOUT_SEC: Final[float] = 15.0
DEFAULT_READ_TIMEOUT_SEC: Final[float] = 30.0
MAX_REDIRECTS: Final[int] = 10

# UI & Throttle Constants
PROGRESS_EMIT_INTERVAL_SEC: Final[float] = 0.25  # 4 Hz throttle
SPEED_WINDOW_SECONDS: Final[float] = 4.0

# Storage & Directory Constants
DEFAULT_TEMP_DIR_NAME: Final[str] = ".pyidm_temp"
DEFAULT_MANIFEST_NAME: Final[str] = "manifest.json"
PART_FILE_SUFFIX: Final[str] = ".part"
ASSEMBLING_SUFFIX: Final[str] = ".assembling"

# Local Browser API
DEFAULT_LOOPBACK_HOST: Final[str] = "127.0.0.1"
DEFAULT_LOOPBACK_PORT: Final[int] = 8743
API_KEY_HEADER_NAME: Final[str] = "X-PyIDM-Key"

