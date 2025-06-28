"""
Dependency injection container for P21 API components.

This module provides a simple dependency injection system to improve
testability and modularity of the application.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Type, TypeVar

if TYPE_CHECKING:
    from .config import Config

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    def register(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        self._services[service_type] = instance

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for creating instances."""
        self._factories[service_type] = factory

    def get(self, service_type: Type[T]) -> T:
        """Get an instance of the requested service."""
        # Check for singleton instance first
        if service_type in self._services:
            return self._services[service_type]  # type: ignore[no-any-return]

        # Check for factory
        if service_type in self._factories:
            return self._factories[service_type]()  # type: ignore[no-any-return]

        raise ValueError(f"Service {service_type} not registered")

    def clear(self) -> None:
        """Clear all registered services (useful for testing)."""
        self._services.clear()
        self._factories.clear()


# Global container instance
container = Container()


class IConfigProvider(ABC):
    """Interface for configuration providers."""

    @abstractmethod
    def get_config(self) -> "Config":
        """Get the application configuration."""
        pass


class IReportRunner(ABC):
    """Interface for report execution."""

    @abstractmethod
    def run_reports(self, report_classes: list, config: "Config") -> list[str]:
        """Run a list of reports and return any exceptions."""
        pass
