"""Integration tests for chunking functionality."""

from unittest.mock import patch

from p21api.odata_client import ODataClient


class TestChunkingIntegration:
    """Integration tests for URL chunking functionality."""

    @patch.object(ODataClient, "fetch_data")
    def test_real_world_grind_shop_scenario(self, mock_fetch_data):
        """Test a real-world scenario similar to the grind shop report."""
        # Mock authentication
        with patch.object(ODataClient, "headers", {"Authorization": "Bearer test"}):
            client = ODataClient("user", "pass", "http://example.com")

            # Create a scenario with many inventory master UIDs (like the real issue)
            many_uids = list(range(1, 301))  # 300 UIDs
            long_filter = (
                "(" + " or ".join([f"inv_mast_uid eq {uid}" for uid in many_uids]) + ")"
            )

            # Mock the fetch_data to return chunked results
            mock_fetch_data.return_value = [
                {"inv_mast_uid": i, "item_id": f"ITEM_{i}"} for i in range(10)
            ]

            # This should trigger chunking due to URL length
            data, url = client.query_odataservice(
                endpoint="p21_view_inv_mast",
                selects=["inv_mast_uid", "item_id", "item_desc"],
                filters=[long_filter],
            )

            # Should have returned data (chunked)
            assert data is not None
            assert len(data) > 0
            assert "(chunked)" in url

            # Should have made multiple calls due to chunking
            assert mock_fetch_data.call_count > 1

    @patch.object(ODataClient, "fetch_data")
    def test_no_chunking_for_short_urls(self, mock_fetch_data):
        """Test that short URLs don't trigger chunking."""
        with patch.object(ODataClient, "headers", {"Authorization": "Bearer test"}):
            client = ODataClient("user", "pass", "http://example.com")

            # Short filter that won't trigger chunking
            short_filter = "(inv_mast_uid eq 1 or inv_mast_uid eq 2)"
            mock_fetch_data.return_value = [{"inv_mast_uid": 1, "item_id": "ITEM_1"}]

            data, url = client.query_odataservice(
                endpoint="p21_view_inv_mast",
                selects=["inv_mast_uid", "item_id"],
                filters=[short_filter],
            )

            # Should not trigger chunking
            assert data is not None
            assert "(chunked)" not in url
            assert mock_fetch_data.call_count == 1

    def test_chunking_performance_reasonable(self):
        """Test that chunking doesn't create unreasonably many requests."""
        client = ODataClient("user", "pass", "http://example.com")

        # Test the chunking logic
        many_conditions = [f"id eq {i}" for i in range(1000)]  # 1000 conditions
        large_filter = "(" + " or ".join(many_conditions) + ")"

        with (
            patch.object(client, "compose_url") as mock_compose,
            patch.object(client, "fetch_data") as mock_fetch,
        ):
            # Mock URLs and data
            mock_compose.return_value = "http://example.com?test"
            mock_fetch.return_value = []

            result = client._try_chunked_request(
                endpoint="test", selects=["id"], filters=[large_filter], chunk_size=50
            )

            # With 1000 conditions and chunk_size=50, should make 20 requests
            expected_chunks = 1000 // 50
            assert mock_fetch.call_count == expected_chunks
            assert mock_fetch.call_count == 20  # Reasonable number of requests
            # Result should be None since no data is returned
            assert result is None
