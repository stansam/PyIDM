"""Core lifecycle and architectural protocols for PyIDM."""

from __future__ import annotations

from typing import Protocol


class Startable(Protocol):
    """Protocol for components that can be started."""

    def start(self) -> None:
        """Start the component lifecycle."""
        ...


class Stoppable(Protocol):
    """Protocol for components that can be gracefully stopped."""

    def stop(self) -> None:
        """Gracefully terminate component lifecycle."""
        ...


class Disposable(Protocol):
    """Protocol for resources requiring deterministic cleanup."""

    def dispose(self) -> None:
        """Release underlying resources, file handles, or network sockets."""
        ...

