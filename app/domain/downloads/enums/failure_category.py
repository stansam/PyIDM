"""Failure classification enum for intelligent retry decisions."""

from enum import StrEnum


class FailureCategory(StrEnum):
    """Categorized error reasons distinguishing transient from permanent failures."""

    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    SERVER_ERROR = "SERVER_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION = "AUTHENTICATION"
    NOT_FOUND = "NOT_FOUND"
    RANGE_REJECTED = "RANGE_REJECTED"
    DISK_FULL = "DISK_FULL"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_CHANGED = "RESOURCE_CHANGED"
    UNKNOWN = "UNKNOWN"

