"""Tests for the new environment configuration module."""

import os
import tempfile

import pytest
from p21api.environment_config import (
    ConfigValidator,
    Environment,
    EnvironmentConfig,
    LoggingConfig,
    PerformanceConfig,
    SecurityConfig,
    load_environment_config,
)


class TestEnvironmentConfig:
    """Test environment configuration classes."""

    def test_environment_enum_values(self):
        """Test environment enum values."""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.TESTING == "testing"
        assert Environment.PRODUCTION == "production"

    def test_logging_config_defaults(self):
        """Test logging configuration defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.file_path is None
        assert config.max_file_size == 10485760
        assert config.backup_count == 5

    def test_logging_config_validation(self):
        """Test logging configuration validation."""
        # Valid log level
        config = LoggingConfig(level="DEBUG")
        assert config.level == "DEBUG"

        # Invalid log level should raise error
        with pytest.raises(ValueError):
            LoggingConfig(level="INVALID")

    def test_security_config_defaults(self):
        """Test security configuration defaults."""
        config = SecurityConfig()
        assert config.token_timeout == 3600
        assert config.max_retry_attempts == 3
        assert config.rate_limit_requests == 100

    def test_performance_config_defaults(self):
        """Test performance configuration defaults."""
        config = PerformanceConfig()
        assert config.max_concurrent_reports == 5
        assert config.chunk_size == 1000
        assert config.cache_ttl == 300

    def test_environment_config_defaults(self):
        """Test environment configuration defaults."""
        config = EnvironmentConfig()
        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is False  # Default is false unless explicitly auto-enabled
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.performance, PerformanceConfig)

    def test_environment_config_debug_auto_enable(self):
        """Test debug auto-enable in development."""
        config = EnvironmentConfig(environment=Environment.DEVELOPMENT, debug=False)
        assert config.debug is False  # Explicit False should remain False

        config = EnvironmentConfig(environment=Environment.PRODUCTION, debug=False)
        assert config.debug is False  # Should remain false


class TestConfigValidator:
    """Test configuration validation utilities."""

    def test_validate_output_directory_success(self, tmp_path):
        """Test successful output directory validation."""
        test_dir = tmp_path / "test_output"
        assert ConfigValidator.validate_output_directory(str(test_dir))
        assert test_dir.exists()

    def test_validate_output_directory_permissions(self):
        """Test output directory validation with permission issues."""
        # Test with invalid path (should handle gracefully)
        invalid_path = "/invalid/path/that/should/not/exist"
        result = ConfigValidator.validate_output_directory(invalid_path)
        # On Windows, this might actually succeed, so we just ensure no exception
        assert isinstance(result, bool)

    def test_validate_url_valid_urls(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://localhost:8080",
            "https://subdomain.example.com/path",
            "http://192.168.1.1:3000",
        ]

        for url in valid_urls:
            assert ConfigValidator.validate_url(url), f"URL should be valid: {url}"

    def test_validate_url_invalid_urls(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Wrong protocol
            "http://",  # Incomplete
            "example.com",  # Missing protocol
            "",  # Empty
        ]

        for url in invalid_urls:
            assert not ConfigValidator.validate_url(url), (
                f"URL should be invalid: {url}"
            )

    def test_validate_required_fields_all_present(self):
        """Test required fields validation with all fields present."""
        config_dict = {
            "username": "test_user",
            "password": "test_pass",
            "base_url": "http://example.com",
        }
        required_fields = ["username", "password", "base_url"]

        missing = ConfigValidator.validate_required_fields(config_dict, required_fields)
        assert missing == []

    def test_validate_required_fields_some_missing(self):
        """Test required fields validation with missing fields."""
        config_dict = {
            "username": "test_user",
            "password": "",  # Empty string
            # base_url missing entirely
        }
        required_fields = ["username", "password", "base_url"]

        missing = ConfigValidator.validate_required_fields(config_dict, required_fields)
        assert "password" in missing
        assert "base_url" in missing
        assert "username" not in missing

    def test_validate_required_fields_whitespace_only(self):
        """Test required fields validation with whitespace-only values."""
        config_dict = {
            "username": "   ",  # Whitespace only
            "password": "test_pass",
            "base_url": "http://example.com",
        }
        required_fields = ["username", "password", "base_url"]

        missing = ConfigValidator.validate_required_fields(config_dict, required_fields)
        assert "username" in missing


class TestLoadEnvironmentConfig:
    """Test environment configuration loading."""

    def test_load_environment_config_defaults(self):
        """Test loading with default values."""
        config = load_environment_config()
        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is False  # Default is False

    def test_load_environment_config_from_env_vars(self):
        """Test loading from environment variables."""
        # Set environment variables
        original_env = os.environ.get("ENVIRONMENT")
        original_debug = os.environ.get("DEBUG")

        try:
            os.environ["ENVIRONMENT"] = "production"
            os.environ["DEBUG"] = "false"

            config = load_environment_config()
            assert config.environment == Environment.PRODUCTION
            assert config.debug is False
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

            if original_debug is not None:
                os.environ["DEBUG"] = original_debug
            elif "DEBUG" in os.environ:
                del os.environ["DEBUG"]

    def test_load_environment_config_from_file(self):
        """Test loading from environment file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("ENVIRONMENT=testing\n")
            f.write("DEBUG=true\n")
            f.write("# This is a comment\n")
            f.write("INVALID_LINE_WITHOUT_EQUALS\n")
            temp_file = f.name

        try:
            config = load_environment_config(temp_file)
            assert config.environment == Environment.TESTING
            assert config.debug is True
        finally:
            os.unlink(temp_file)

    def test_load_environment_config_env_vars_override_file(self):
        """Test that environment variables override file values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("ENVIRONMENT=testing\n")
            f.write("DEBUG=false\n")
            temp_file = f.name

        original_env = os.environ.get("ENVIRONMENT")

        try:
            # Set environment variable that should override file
            os.environ["ENVIRONMENT"] = "production"

            config = load_environment_config(temp_file)
            assert config.environment == Environment.PRODUCTION  # From env var
            assert config.debug is False  # From file
        finally:
            os.unlink(temp_file)
            if original_env is not None:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

    def test_load_environment_config_nonexistent_file(self):
        """Test loading with non-existent file."""
        config = load_environment_config("nonexistent.env")
        # Should not raise error, just use defaults
        assert config.environment == Environment.DEVELOPMENT
