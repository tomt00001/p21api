"""Tests for the dependency injection container module."""

import pytest
from p21api.container import Container, IConfigProvider, IReportRunner


class MockConfigProvider(IConfigProvider):
    """Mock config provider for testing."""

    def __init__(self):
        self.test_config: dict = {}

    def get_config(self):
        return {"test": "config"}


class MockReportRunner(IReportRunner):
    """Mock report runner for testing."""

    def run_reports(self, report_classes, config):
        return []


class TestContainer:
    """Test the dependency injection container."""

    def test_init(self):
        """Test container initialization."""
        container = Container()
        assert container._services == {}
        assert container._factories == {}

    def test_register_singleton(self):
        """Test registering a singleton instance."""
        container = Container()
        mock_provider = MockConfigProvider()

        container.register(IConfigProvider, mock_provider)

        # Should return the same instance
        result = container.get(IConfigProvider)
        assert result is mock_provider

        # Should return the same instance on subsequent calls
        result2 = container.get(IConfigProvider)
        assert result2 is mock_provider

    def test_register_factory(self):
        """Test registering a factory function."""
        container = Container()

        def create_provider():
            return MockConfigProvider()

        container.register_factory(IConfigProvider, create_provider)

        # Should create a new instance each time
        result1 = container.get(IConfigProvider)
        result2 = container.get(IConfigProvider)

        assert isinstance(result1, MockConfigProvider)
        assert isinstance(result2, MockConfigProvider)
        assert result1 is not result2  # Different instances

    def test_singleton_takes_precedence(self):
        """Test that singleton registration takes precedence over factory."""
        container = Container()
        mock_provider = MockConfigProvider()

        # Register both factory and singleton
        container.register_factory(IConfigProvider, lambda: MockConfigProvider())
        container.register(IConfigProvider, mock_provider)

        # Should return the singleton instance
        result = container.get(IConfigProvider)
        assert result is mock_provider

    def test_get_unregistered_service(self):
        """Test getting an unregistered service raises ValueError."""
        container = Container()

        with pytest.raises(ValueError, match="Service .* not registered"):
            container.get(IConfigProvider)

    def test_clear_services(self):
        """Test clearing all registered services."""
        container = Container()
        mock_provider = MockConfigProvider()

        container.register(IConfigProvider, mock_provider)
        container.register_factory(IReportRunner, lambda: MockReportRunner())

        # Verify services are registered
        assert len(container._services) == 1
        assert len(container._factories) == 1

        # Clear all services
        container.clear()

        # Verify services are cleared
        assert len(container._services) == 0
        assert len(container._factories) == 0

        # Getting service should now fail
        with pytest.raises(ValueError):
            container.get(IConfigProvider)

    def test_multiple_service_types(self):
        """Test registering multiple different service types."""
        container = Container()

        mock_provider = MockConfigProvider()
        mock_runner = MockReportRunner()

        container.register(IConfigProvider, mock_provider)
        container.register(IReportRunner, mock_runner)

        # Should be able to get both services
        provider_result = container.get(IConfigProvider)
        runner_result = container.get(IReportRunner)

        assert provider_result is mock_provider
        assert runner_result is mock_runner

    def test_factory_with_parameters(self):
        """Test factory function that uses closure parameters."""
        container = Container()

        config_data = {"environment": "test"}

        def create_provider():
            provider = MockConfigProvider()
            provider.test_config = config_data
            return provider

        container.register_factory(IConfigProvider, create_provider)

        result = container.get(IConfigProvider)
        assert hasattr(result, "test_config")
        assert result.test_config == config_data  # type: ignore[attr-defined]


class TestGlobalContainer:
    """Test the global container instance."""

    def setup_method(self):
        """Clear the global container before each test."""
        from p21api.container import container

        container.clear()

    def test_global_container_usage(self):
        """Test using the global container instance."""
        from p21api.container import container

        mock_provider = MockConfigProvider()
        container.register(IConfigProvider, mock_provider)

        result = container.get(IConfigProvider)
        assert result is mock_provider

    def test_global_container_isolation(self):
        """Test that global container is isolated between tests."""
        from p21api.container import container

        # This test should start with empty container due to setup_method
        with pytest.raises(ValueError):
            container.get(IConfigProvider)


class TestInterfaces:
    """Test the interface definitions."""

    def test_iconfig_provider_interface(self):
        """Test IConfigProvider interface."""
        provider = MockConfigProvider()
        config = provider.get_config()
        assert config == {"test": "config"}

    def test_ireport_runner_interface(self):
        """Test IReportRunner interface."""
        runner = MockReportRunner()
        result = runner.run_reports([], None)  # type: ignore[arg-type]
        assert result == []

    def test_interfaces_are_abstract(self):
        """Test that interfaces cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IConfigProvider()  # type: ignore[abstract]

        with pytest.raises(TypeError):
            IReportRunner()  # type: ignore[abstract]
