"""
Environment-specific configuration and validation utilities.

This module provides enhanced configuration validation and environment-specific
settings management for the P21 API application.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Environment(str, Enum):
    """Supported environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    host: str = Field(..., description="Database host")
    port: int = Field(default=1433, description="Database port")
    database: str = Field(..., description="Database name")
    timeout: int = Field(default=30, description="Connection timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(
        default=10485760, description="Max log file size in bytes (10MB)"
    )
    backup_count: int = Field(default=5, description="Number of backup log files")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class SecurityConfig(BaseModel):
    """Security-related configuration."""

    token_timeout: int = Field(default=3600, description="Token timeout in seconds")
    max_retry_attempts: int = Field(
        default=3, description="Max retry attempts for auth"
    )
    rate_limit_requests: int = Field(default=100, description="Max requests per minute")


class PerformanceConfig(BaseModel):
    """Performance-related configuration."""

    max_concurrent_reports: int = Field(
        default=5, description="Max concurrent report executions"
    )
    chunk_size: int = Field(default=1000, description="Data processing chunk size")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""

    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    database: Optional[DatabaseConfig] = Field(default=None)

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, v: bool | None) -> bool:
        """Auto-enable debug in development."""
        # Note: In Pydantic V2, field validators don't receive other field values
        # The environment-specific logic should be handled elsewhere if needed
        return bool(v) if v is not None else False

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_output_directory(path: str) -> bool:
        """Validate that output directory exists and is writable."""
        try:
            path_obj = Path(path)
            path_obj.mkdir(parents=True, exist_ok=True)

            # Test write permissions
            test_file = path_obj / ".write_test"
            test_file.touch()
            test_file.unlink()

            return True
        except (OSError, PermissionError):
            return False

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return url_pattern.match(url) is not None

    @staticmethod
    def validate_required_fields(
        config_dict: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate that required fields are present and not empty."""
        missing_fields: list[str] = []
        for field in required_fields:
            value = config_dict.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        return missing_fields


def load_environment_config(env_file: Optional[str] = None) -> EnvironmentConfig:
    """Load environment-specific configuration."""
    env_vars: dict[str, str] = {}

    # Load from environment file if specified
    if env_file and os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    # Override with actual environment variables
    env_vars.update(os.environ)

    # Map environment variables to config with explicit typing
    environment = Environment(env_vars.get("ENVIRONMENT", Environment.DEVELOPMENT))
    debug = env_vars.get("DEBUG", "false").lower() == "true"

    return EnvironmentConfig(
        environment=environment,
        debug=debug,
        logging=LoggingConfig(),
        security=SecurityConfig(),
        performance=PerformanceConfig(),
        database=None,
    )
