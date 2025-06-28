"""Tests for OData client functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from p21api.odata_client import ODataClient


class TestODataClient:
    """Test cases for ODataClient class."""

    def test_init(self):
        """Test ODataClient initialization."""
        client = ODataClient("user", "pass", "http://example.com")
        assert client.username == "user"
        assert client.password == "pass"
        assert client.base_url == "http://example.com"

    @patch("p21api.odata_client.requests.post")
    def test_get_headers_success(self, mock_post, mock_requests_response):
        """Test successful authentication and header retrieval."""
        mock_post.return_value = mock_requests_response

        client = ODataClient("user", "pass", "http://example.com")
        headers = client.headers

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token_value"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

        mock_post.assert_called_once_with(
            "http://example.com/api/security/token",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "username": "user",
                "password": "pass",
            },
            timeout=30,
        )

    @patch("p21api.odata_client.requests.post")
    def test_get_headers_failure(self, mock_post, mock_requests_auth_failure):
        """Test authentication failure."""
        mock_post.return_value = mock_requests_auth_failure

        client = ODataClient("user", "pass", "http://example.com")

        with pytest.raises(Exception, match="Failed to obtain token"):
            _ = client.headers

    @patch("p21api.odata_client.requests.get")
    def test_fetch_data_success(self, mock_get, mock_odata_client):
        """Test successful data fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": [{"data": "test"}]}
        mock_get.return_value = mock_response

        client = ODataClient("user", "pass", "http://example.com")
        client.headers = {"Authorization": "Bearer test_token"}

        result = client.fetch_data("http://example.com/api/data")

        assert result == [{"data": "test"}]
        mock_get.assert_called_once_with(
            "http://example.com/api/data",
            headers={"Authorization": "Bearer test_token"},
            timeout=60,
        )

    @patch("p21api.odata_client.requests.get")
    def test_fetch_data_failure(self, mock_get):
        """Test data fetching failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        client = ODataClient("user", "pass", "http://example.com")
        client.headers = {"Authorization": "Bearer test_token"}

        with pytest.raises(Exception, match="Failed to fetch data"):
            client.fetch_data("http://example.com/api/nonexistent")

    def test_get_endpoint_url(self):
        """Test endpoint URL construction."""
        client = ODataClient("user", "pass", "http://example.com")
        url = client._get_endpoint_url("test_endpoint")
        assert url == "http://example.com/odataservice/odata/view/test_endpoint"

    def test_get_selects(self):
        """Test select clause construction."""
        client = ODataClient("user", "pass", "http://example.com")
        selects = client._get_selects(["field1", "field2", "field3"])
        assert selects == "$select=field1,field2,field3"

    def test_get_startdate_filter(self):
        """Test start date filter construction."""
        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31, 23, 59, 59, 999999)

        filter_list = client._get_startdate_filter(start_date, end_date)
        expected = [
            "date_created ge 2024-01-01T00:00:00Z",
            "date_created le 2024-01-31T23:59:59Z",
        ]
        assert filter_list == expected

    def test_get_filters(self):
        """Test additional filters construction."""
        client = ODataClient("user", "pass", "http://example.com")
        filters = client._get_filters(["status eq 'active'", "type eq 'invoice'"])
        assert filters == "$filter=status eq 'active' and type eq 'invoice'"

    def test_get_order_by(self):
        """Test order by clause construction."""
        client = ODataClient("user", "pass", "http://example.com")
        order_by = client._get_order_by(["field1 asc", "field2 desc"])
        assert order_by == "$orderby=field1 asc,field2 desc"

    def test_compose_url_minimal(self):
        """Test URL composition with minimal parameters."""
        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)

        url = client.compose_url("test_endpoint", ["field1", "field2"], start_date)

        assert "test_endpoint" in url
        assert "$select=field1,field2" in url
        assert "date_created ge 2024-01-01T00:00:00Z" in url

    def test_compose_url_full(self):
        """Test URL composition with all parameters."""
        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)

        url = client.compose_url(
            "test_endpoint",
            ["field1", "field2"],
            start_date,
            filters=["status eq 'active'"],
            order_by=["field1 asc"],
        )

        assert "test_endpoint" in url
        assert "$select=field1,field2" in url
        assert "status eq 'active'" in url
        assert "$orderby=field1 asc" in url
        assert "date_created ge 2024-01-01T00:00:00Z" in url
        assert "status eq 'active'" in url
        assert "$orderby=field1 asc" in url

    def test_get_datetime_filter(self):
        """Test datetime filter generation."""
        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31, 23, 59, 59, 999999)

        filter_list = client.get_datetime_filter("test_date", start_date, end_date)
        expected = [
            "test_date ge 2024-01-01T00:00:00Z",
            "test_date le 2024-01-31T23:59:59Z",
        ]
        assert filter_list == expected

    def test_datetime_to_str(self):
        """Test datetime to string conversion."""
        client = ODataClient("user", "pass", "http://example.com")
        dt = datetime(2024, 1, 15, 14, 30, 45, 123456)
        result = client._datetime_to_str(dt)
        assert result == "2024-01-15T14:30:45Z"

    def test_get_current_month_end_date(self):
        """Test current month end date calculation."""
        client = ODataClient("user", "pass", "http://example.com")

        # Test January (31 days)
        jan_date = datetime(2024, 1, 15)
        jan_end = client.get_current_month_end_date(jan_date)
        assert jan_end == datetime(2024, 1, 31, 23, 59, 59, 999999)

        # Test February (29 days in 2024 - leap year)
        feb_date = datetime(2024, 2, 10)
        feb_end = client.get_current_month_end_date(feb_date)
        assert feb_end == datetime(2024, 2, 29, 23, 59, 59, 999999)

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_query_odataservice(
        self, mock_compose_url, mock_fetch_data, sample_invoice_data
    ):
        """Test OData service querying."""
        mock_compose_url.return_value = "http://example.com/api/test"
        mock_fetch_data.return_value = sample_invoice_data

        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)

        data, url = client.query_odataservice(
            "test_endpoint", start_date=start_date, selects=["field1", "field2"]
        )

        assert data == sample_invoice_data
        assert url == "http://example.com/api/test"
        mock_compose_url.assert_called_once()
        mock_fetch_data.assert_called_once_with("http://example.com/api/test")

    @patch.object(ODataClient, "fetch_data")
    def test_query_odataservice_no_data(self, mock_fetch_data):
        """Test OData service querying with no data returned."""
        mock_fetch_data.return_value = None

        client = ODataClient("user", "pass", "http://example.com")
        start_date = datetime(2024, 1, 1)

        data, url = client.query_odataservice(
            "test_endpoint", start_date, selects=["field1"]
        )

        assert data is None
        assert url is not None

    @patch("p21api.odata_client.requests.post")
    def test_post_odataservice(self, mock_post):
        """Test OData service POST operation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [{"success": True}],
            "@odata.count": 1,
        }
        mock_post.return_value = mock_response

        client = ODataClient("user", "pass", "http://example.com")
        client.headers = {"Authorization": "Bearer test_token"}

        result = client.post_odataservice("test_endpoint", ["field1", "field2"])

        assert result == [{"success": True}]
        mock_post.assert_called()

    def test_headers_cached_property(self):
        """Test that headers are cached and not recalculated."""
        with patch.object(ODataClient, "_get_headers") as mock_get_headers:
            mock_get_headers.return_value = {"Authorization": "Bearer test"}

            client = ODataClient("user", "pass", "http://example.com")

            # First access
            headers1 = client.headers
            # Second access
            headers2 = client.headers

            assert headers1 == headers2
            # Should only be called once due to caching
            mock_get_headers.assert_called_once()
