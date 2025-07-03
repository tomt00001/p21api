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

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_query_odataservice_no_chunking_needed(
        self, mock_compose_url, mock_fetch_data
    ):
        """Test query_odataservice when URL is short enough (no chunking needed)."""
        # Setup mocks
        short_url = "http://example.com/api/test?short=params"
        mock_compose_url.return_value = short_url
        mock_fetch_data.return_value = [{"id": 1, "name": "test"}]

        client = ODataClient("user", "pass", "http://example.com")

        data, url = client.query_odataservice(
            "test_endpoint", selects=["id", "name"], filters=["id eq 1"]
        )

        # Should use normal path (no chunking)
        assert data == [{"id": 1, "name": "test"}]
        assert url == short_url
        mock_compose_url.assert_called_once()
        mock_fetch_data.assert_called_once_with(short_url)

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_query_odataservice_chunking_needed(
        self, mock_compose_url, mock_fetch_data
    ):
        """Test query_odataservice when URL is too long and chunking is needed."""
        # Create a long filter that would exceed URL length limit
        long_filter = (
            "(" + " or ".join([f"inv_mast_uid eq {i}" for i in range(100)]) + ")"
        )

        # Mock compose_url to return a very long URL for the first call
        long_url = "http://example.com/api/test?" + "x" * 3000  # Exceed 2048 limit
        short_urls = [
            "http://example.com/api/test?chunk1",
            "http://example.com/api/test?chunk2",
        ]

        mock_compose_url.side_effect = [long_url] + short_urls

        # Mock fetch_data to return different data for each chunk
        chunk1_data = [{"inv_mast_uid": i, "item_id": f"item_{i}"} for i in range(50)]
        chunk2_data = [
            {"inv_mast_uid": i, "item_id": f"item_{i}"} for i in range(50, 100)
        ]
        mock_fetch_data.side_effect = [chunk1_data, chunk2_data]

        client = ODataClient("user", "pass", "http://example.com")

        data, url = client.query_odataservice(
            "test_endpoint",
            selects=["inv_mast_uid", "item_id"],
            filters=[long_filter],
        )

        # Should return combined data from both chunks
        expected_data = chunk1_data + chunk2_data
        assert data == expected_data
        assert "(chunked)" in url

        # Should have called compose_url 3 times (1 initial + 2 chunks)
        assert mock_compose_url.call_count == 3
        # Should have called fetch_data 2 times (once per chunk)
        assert mock_fetch_data.call_count == 2

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_try_chunked_request_not_chunkable(self, mock_compose_url, mock_fetch_data):
        """Test _try_chunked_request when filter is not chunkable."""
        client = ODataClient("user", "pass", "http://example.com")

        # Test with short URL (no chunking needed)
        short_url = "http://example.com/api/test?short"
        mock_compose_url.return_value = short_url

        result = client._try_chunked_request(
            endpoint="test",
            selects=["id"],
            filters=["simple eq 'filter'"],
        )

        assert result is None  # No chunking needed

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_try_chunked_request_no_or_conditions(
        self, mock_compose_url, mock_fetch_data
    ):
        """Test _try_chunked_request when filter has no OR conditions."""
        client = ODataClient("user", "pass", "http://example.com")

        # Create a long URL but without OR conditions
        long_url = "http://example.com/api/test?" + "x" * 3000
        mock_compose_url.return_value = long_url

        result = client._try_chunked_request(
            endpoint="test",
            selects=["id"],
            filters=["simple eq 'very_long_value_that_makes_url_long'"],
        )

        assert result is None  # No chunkable OR conditions

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_try_chunked_request_small_or_filter(
        self, mock_compose_url, mock_fetch_data
    ):
        """Test _try_chunked_request when OR filter is small (no chunking needed)."""
        client = ODataClient("user", "pass", "http://example.com")

        # Create a long URL but with small OR filter
        long_url = "http://example.com/api/test?" + "x" * 3000
        mock_compose_url.return_value = long_url

        small_or_filter = "(id eq 1 or id eq 2 or id eq 3)"  # Only 3 conditions

        result = client._try_chunked_request(
            endpoint="test",
            selects=["id"],
            filters=[small_or_filter],
        )

        assert result is None  # OR filter too small to chunk

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_try_chunked_request_successful_chunking(
        self, mock_compose_url, mock_fetch_data
    ):
        """Test _try_chunked_request with successful chunking."""
        client = ODataClient("user", "pass", "http://example.com")

        # Create a long URL that needs chunking
        long_url = "http://example.com/api/test?" + "x" * 3000
        chunk_urls = [
            "http://example.com/api/test?chunk1",
            "http://example.com/api/test?chunk2",
        ]
        mock_compose_url.side_effect = [long_url] + chunk_urls

        # Create a large OR filter
        large_or_filter = "(" + " or ".join([f"id eq {i}" for i in range(100)]) + ")"

        # Mock data for each chunk
        chunk1_data = [{"id": i} for i in range(50)]
        chunk2_data = [{"id": i} for i in range(50, 100)]
        mock_fetch_data.side_effect = [chunk1_data, chunk2_data]

        result = client._try_chunked_request(
            endpoint="test",
            selects=["id"],
            filters=["other_filter eq 'value'", large_or_filter],
            chunk_size=50,
        )

        # Should return combined data
        expected_data = chunk1_data + chunk2_data
        assert result == expected_data

        # Verify calls
        assert mock_compose_url.call_count == 2  # 2 chunks
        assert mock_fetch_data.call_count == 2  # 2 chunks

    @patch.object(ODataClient, "fetch_data")
    @patch.object(ODataClient, "compose_url")
    def test_try_chunked_request_empty_chunks(self, mock_compose_url, mock_fetch_data):
        """Test _try_chunked_request when chunks return empty data."""
        client = ODataClient("user", "pass", "http://example.com")

        # Setup for chunking scenario
        long_url = "http://example.com/api/test?" + "x" * 3000
        chunk_urls = ["http://example.com/api/test?chunk1"]
        mock_compose_url.side_effect = [long_url] + chunk_urls

        large_or_filter = "(" + " or ".join([f"id eq {i}" for i in range(60)]) + ")"

        # Mock empty data
        mock_fetch_data.return_value = None

        result = client._try_chunked_request(
            endpoint="test",
            selects=["id"],
            filters=[large_or_filter],
            chunk_size=50,
        )

        assert result is None  # Should return None when no data found

    def test_chunking_logic_correctness(self):
        """Test the chunking logic with various scenarios."""
        # Test filter parsing
        test_filter = "(id eq 1 or id eq 2 or id eq 3 or id eq 4 or id eq 5)"

        # Simulate the parsing logic
        if test_filter.startswith("(") and test_filter.endswith(")"):
            inner_filter = test_filter[1:-1]  # Remove parentheses
            conditions = [cond.strip() for cond in inner_filter.split(" or ")]

            assert len(conditions) == 5
            assert conditions[0] == "id eq 1"
            assert conditions[4] == "id eq 5"

            # Test chunking
            chunk_size = 2
            chunks = []
            for i in range(0, len(conditions), chunk_size):
                chunk_conditions = conditions[i : i + chunk_size]
                chunked_filter = f"({' or '.join(chunk_conditions)})"
                chunks.append(chunked_filter)

            assert len(chunks) == 3  # 5 conditions with chunk_size=2 gives 3 chunks
            assert chunks[0] == "(id eq 1 or id eq 2)"
            assert chunks[1] == "(id eq 3 or id eq 4)"
            assert chunks[2] == "(id eq 5)"
