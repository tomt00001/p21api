"""Tests for configuration validation schemas."""

from p21api.config_validator import (
    get_config_recommendations,
    validate_config_dict,
)


class TestValidateConfigDict:
    """Test the validate_config_dict function."""

    def test_valid_config_dict(self):
        """Test validation of a valid config dictionary."""
        config_dict = {
            "base_url": "https://example.com/odata",
            "username": "test_user",
            "password": "test_password",
            "output_folder": "/tmp/reports",
            "start_date": "2024-01-01",
            "report_groups": ["monthly"],
            "debug": False,
            "max_workers": 5,
        }
        result = validate_config_dict(config_dict)

        assert "connection" in result["valid"]
        assert "reports" in result["valid"]
        assert "application" in result["valid"]
        assert len(result["errors"]) == 0

    def test_missing_connection_fields(self):
        """Test validation with missing connection fields."""
        config_dict = {
            "base_url": "",  # Empty
            "username": "test_user",
            "password": "test_password",
            "output_folder": "/tmp/reports",
            "start_date": "2024-01-01",
        }
        result = validate_config_dict(config_dict)

        assert "connection" not in result["valid"]
        assert any("Missing required fields" in error for error in result["errors"])

    def test_invalid_url_format(self):
        """Test validation with invalid URL format."""
        config_dict = {
            "base_url": "invalid-url",  # Invalid URL
            "username": "test_user",
            "password": "test_password",
            "output_folder": "/tmp/reports",
            "start_date": "2024-01-01",
        }
        result = validate_config_dict(config_dict)

        assert any("Connection.base_url" in error for error in result["errors"])

    def test_invalid_date_format(self):
        """Test validation with invalid date format."""
        config_dict = {
            "base_url": "https://example.com/odata",
            "username": "test_user",
            "password": "test_password",
            "output_folder": "/tmp/reports",
            "start_date": "invalid-date",  # Invalid date format
        }
        result = validate_config_dict(config_dict)

        assert any("Reports.start_date" in error for error in result["errors"])

    def test_invalid_max_workers(self):
        """Test validation with invalid max_workers."""
        config_dict = {
            "base_url": "https://example.com/odata",
            "username": "test_user",
            "password": "test_password",
            "output_folder": "/tmp/reports",
            "start_date": "2024-01-01",
            "max_workers": 0,  # Invalid worker count
        }
        result = validate_config_dict(config_dict)

        assert any("Application.max_workers" in error for error in result["errors"])

    def test_empty_config_dict(self):
        """Test validation with empty config dictionary."""
        config_dict = {}
        result = validate_config_dict(config_dict)

        # Application section has defaults so it may be valid
        assert len(result["errors"]) > 0  # Should have connection/report errors
        assert "connection" not in result["valid"]
        assert "reports" not in result["valid"]

    def test_partial_valid_config(self):
        """Test validation with partially valid config."""
        config_dict = {
            "base_url": "https://example.com/odata",
            "username": "test_user",
            "password": "test_password",
            # Missing report config
            "debug": False,
            "max_workers": 5,
        }
        result = validate_config_dict(config_dict)

        assert "connection" in result["valid"]
        assert "application" in result["valid"]
        assert "reports" not in result["valid"]


class TestGetConfigRecommendations:
    """Test the get_config_recommendations function."""

    def test_high_max_workers_recommendation(self):
        """Test recommendation for high max_workers."""
        config_dict = {"max_workers": 15}
        recommendations = get_config_recommendations(config_dict)

        assert any("reducing max_workers" in rec for rec in recommendations)

    def test_debug_mode_recommendation(self):
        """Test recommendation for debug mode in production."""
        config_dict = {"debug": True}
        recommendations = get_config_recommendations(config_dict)

        assert any("Disable debug mode" in rec for rec in recommendations)

    def test_http_url_recommendation(self):
        """Test recommendation for HTTP URLs."""
        config_dict = {"base_url": "http://example.com/odata"}
        recommendations = get_config_recommendations(config_dict)

        assert any("HTTPS" in rec for rec in recommendations)

    def test_no_recommendations_for_optimal_config(self):
        """Test no recommendations for optimal configuration."""
        config_dict = {
            "max_workers": 5,
            "debug": False,
            "base_url": "https://example.com/odata",
        }
        recommendations = get_config_recommendations(config_dict)

        assert len(recommendations) == 0

    def test_multiple_recommendations(self):
        """Test multiple recommendations for suboptimal configuration."""
        config_dict = {
            "max_workers": 15,  # Too high
            "debug": True,  # Should be disabled in prod
            "base_url": "http://example.com/odata",  # Should use HTTPS
        }
        recommendations = get_config_recommendations(config_dict)

        assert len(recommendations) >= 2  # Should have multiple recommendations

    def test_recommendations_with_missing_values(self):
        """Test recommendations with missing configuration values."""
        config_dict = {}
        recommendations = get_config_recommendations(config_dict)

        # Should not crash and return empty or minimal recommendations
        assert isinstance(recommendations, list)
