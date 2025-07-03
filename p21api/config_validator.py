"""Configuration schema validation utilities."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class P21ConnectionSchema(BaseModel):
    """Schema for P21 connection configuration."""

    base_url: str = Field(..., description="P21 OData API base URL")
    username: str = Field(..., description="P21 username")
    password: str = Field(..., description="P21 password")

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if not v.endswith("/"):
            v = v + "/"
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username is not empty."""
        if not v or not v.strip():
            raise ValueError("username cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets minimum requirements."""
        if not v or len(v) < 3:
            raise ValueError("password must be at least 3 characters")
        return v


class ReportConfigSchema(BaseModel):
    """Schema for report configuration."""

    output_folder: str = Field(..., description="Output folder path")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    report_groups: List[str] = Field(
        default=["monthly"], description="List of report groups to execute"
    )

    @field_validator("output_folder")
    @classmethod
    def validate_output_folder(cls, v: str) -> str:
        """Validate output folder path."""
        if not v or not v.strip():
            raise ValueError("output_folder cannot be empty")
        return v.strip()

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: str) -> str:
        """Validate start date format."""
        from datetime import datetime

        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: str | None) -> str | None:
        """Validate end date format."""
        if v is None:
            return v
        from datetime import datetime

        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format")
        return v

    @field_validator("report_groups")
    @classmethod
    def validate_report_groups(cls, v: list[str]) -> list[str]:
        """Validate report groups."""
        valid_groups = ["monthly", "inventory", "po"]
        invalid_groups = [group for group in v if group not in valid_groups]
        if invalid_groups:
            valid_str = ", ".join(valid_groups)
            invalid_str = ", ".join(invalid_groups)
            msg = f"Invalid report groups: {invalid_str}. Valid: {valid_str}"
            raise ValueError(msg)
        return v


class ApplicationConfigSchema(BaseModel):
    """Schema for application configuration."""

    debug: bool = Field(default=False, description="Enable debug mode")
    show_gui: bool = Field(default=False, description="Show GUI interface")
    max_workers: int = Field(default=5, description="Maximum concurrent workers")

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v: int) -> int:
        """Validate max workers is reasonable."""
        if v < 1:
            raise ValueError("max_workers must be at least 1")
        if v > 20:
            raise ValueError("max_workers should not exceed 20 for stability")
        return v


class FullConfigSchema(BaseModel):
    """Complete configuration schema."""

    connection: P21ConnectionSchema
    reports: ReportConfigSchema
    application: ApplicationConfigSchema = Field(
        default_factory=ApplicationConfigSchema
    )


def validate_config_dict(config_dict: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate a configuration dictionary against schemas.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        Dictionary with validation results:
        - 'valid': List of valid sections
        - 'errors': List of error messages
    """
    results: Dict[str, List[str]] = {"valid": [], "errors": []}

    # Validate connection config
    try:
        connection_data: Dict[str, str] = {
            "base_url": config_dict.get("base_url", ""),
            "username": config_dict.get("username", ""),
            "password": config_dict.get("password", ""),
        }
        # Skip validation if any required field is missing
        if not all(connection_data.values()):
            results["errors"].append("Connection: Missing required fields")
        else:
            P21ConnectionSchema(**connection_data)
            results["valid"].append("connection")
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            results["errors"].append(f"Connection.{field}: {message}")

    # Validate report config
    try:
        report_data: Dict[str, Any] = {
            "output_folder": config_dict.get("output_folder", ""),
            "start_date": config_dict.get("start_date", ""),
            "end_date": config_dict.get("end_date"),
            "report_groups": config_dict.get("report_groups", ["monthly"]),
        }
        ReportConfigSchema(**report_data)
        results["valid"].append("reports")
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            results["errors"].append(f"Reports.{field}: {message}")

    # Validate application config
    try:
        app_data: Dict[str, Any] = {
            "debug": config_dict.get("debug", False),
            "show_gui": config_dict.get("show_gui", False),
            "max_workers": config_dict.get("max_workers", 5),
        }
        ApplicationConfigSchema(**app_data)
        results["valid"].append("application")
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            results["errors"].append(f"Application.{field}: {message}")

    return results


def get_config_recommendations(config_dict: Dict[str, Any]) -> List[str]:
    """
    Get configuration recommendations for optimization.

    Args:
        config_dict: Configuration dictionary

    Returns:
        List of recommendation messages
    """
    recommendations: List[str] = []

    # Performance recommendations
    max_workers = config_dict.get("max_workers", 5)
    if max_workers > 10:
        recommendations.append(
            "Consider reducing max_workers for better stability (recommended: 5-10)"
        )

    # Security recommendations
    if config_dict.get("debug", False):
        recommendations.append("Disable debug mode in production for better security")

    # URL recommendations
    base_url = config_dict.get("base_url", "")
    if base_url.startswith("http://"):
        recommendations.append("Consider using HTTPS for better security")

    return recommendations
