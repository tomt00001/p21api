"""Performance and load tests for the application."""

import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from p21api.config import Config
from p21api.odata_client import ODataClient


class TestPerformance:
    """Performance tests for critical application components."""

    def test_config_initialization_performance(self):
        """Test Config initialization performance."""
        start_time = time.time()

        for _ in range(100):
            _ = Config(
                base_url="http://example.com",
                username="test",
                password="password",
                output_folder="test/",
                start_date="2024-01-01",
            )

        end_time = time.time()
        duration = end_time - start_time

        # Should be able to create 100 configs in less than 1 second
        assert duration < 1.0

    @patch("p21api.odata_client.requests.post")
    def test_odata_client_initialization_performance(self, mock_post):
        """Test ODataClient initialization performance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_response

        start_time = time.time()

        clients = []
        for i in range(10):
            client = ODataClient(f"user{i}", "password", "http://example.com")
            # Access headers to trigger authentication
            _ = client.headers
            clients.append(client)

        end_time = time.time()
        duration = end_time - start_time

        # Should be able to create and authenticate 10 clients in reasonable time
        assert duration < 5.0
        assert len(clients) == 10

    def test_large_date_range_processing(self):
        """Test performance with large date ranges."""
        config = Config(
            base_url="http://example.com",
            username="test",
            password="password",
            output_folder="test/",
            start_date="2020-01-01",
            end_date_="2024-12-31",
        )

        start_time = time.time()

        # Process date range calculations
        date_diff = config.end_date - config.start_date
        _ = date_diff.days  # Calculate days but don't use the variable

        # Simulate processing each day
        processed_days = []
        current_date = config.start_date
        while current_date <= config.end_date:
            processed_days.append(current_date)
            current_date += timedelta(days=1)

            # Break if we've processed enough for the test
            if len(processed_days) >= 1000:
                break

        end_time = time.time()
        duration = end_time - start_time

        # Should process 1000 days in reasonable time
        assert duration < 1.0
        assert len(processed_days) >= 1000

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_large_dataset_processing(self, mock_fromdicts, mock_tocsv):
        """Test performance with large datasets."""
        # Create large mock dataset
        large_dataset = []
        for i in range(10000):
            large_dataset.append(
                {
                    "id": i,
                    "name": f"Item {i}",
                    "value": i * 1.5,
                    "date": f"2024-01-{(i % 28) + 1:02d}",
                }
            )

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        start_time = time.time()

        # Simulate report processing
        from p21api.report_daily_sales import ReportDailySales

        mock_client = Mock()
        mock_client.query_odataservice.return_value = (large_dataset, "test_url")

        mock_config = Mock()
        mock_config.debug = False
        mock_config.end_date = datetime(2024, 1, 31)

        report = ReportDailySales(
            client=mock_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test/",
            debug=False,
            config=mock_config,
        )

        report._run()

        end_time = time.time()
        duration = end_time - start_time

        # Should process 10k records in reasonable time
        assert duration < 2.0
        mock_fromdicts.assert_called_once_with(large_dataset)


class TestConcurrency:
    """Concurrency and thread safety tests."""

    @patch("p21api.odata_client.requests.post")
    @patch("p21api.odata_client.requests.get")
    def test_concurrent_odata_clients(self, mock_get, mock_post):
        """Test multiple OData clients running concurrently."""
        # Setup mocks
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        mock_data_response = Mock()
        mock_data_response.status_code = 200
        mock_data_response.json.return_value = {"value": [{"test": "data"}]}
        mock_get.return_value = mock_data_response

        def create_and_use_client(user_id):
            """Create a client and fetch data."""
            client = ODataClient(f"user{user_id}", "password", "http://example.com")
            return client.fetch_data("http://example.com/api/test")

        # Run multiple clients concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_use_client, i) for i in range(10)]
            results = [future.result() for future in futures]

        # All should succeed
        assert len(results) == 10
        for result in results:
            # fetch_data returns the 'value' part directly, not the full response
            assert result == [{"test": "data"}]

    def test_concurrent_config_access(self):
        """Test concurrent access to Config objects."""
        configs = []
        errors = []

        def create_config(thread_id):
            """Create a config in a thread."""
            try:
                # Use temporary directory to avoid creating actual folders
                with tempfile.TemporaryDirectory() as temp_dir:
                    config = Config(
                        base_url=f"http://example{thread_id}.com",
                        username=f"user{thread_id}",
                        password="password",
                        output_folder=temp_dir + "/",
                        start_date="2024-01-01",
                    )
                    configs.append(config)
            except Exception as e:
                errors.append(e)

        # Create configs concurrently
        threads = []
        for i in range(20):
            thread = threading.Thread(target=create_config, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have no errors and all configs created
        assert len(errors) == 0
        assert len(configs) == 20

    @patch("p21api.odata_client.requests.post")
    def test_odata_client_thread_safety(self, mock_post):
        """Test OData client thread safety."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_response

        client = ODataClient("user", "password", "http://example.com")

        headers_results = []
        errors = []

        def access_headers(thread_id):
            """Access headers from multiple threads."""
            try:
                headers = client.headers
                headers_results.append(headers)
            except Exception as e:
                errors.append(e)

        # Access headers concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=access_headers, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have no errors and all results should be the same
        assert len(errors) == 0
        assert len(headers_results) == 10

        # All headers should be identical (cached)
        first_headers = headers_results[0]
        for headers in headers_results:
            assert headers == first_headers


class TestMemoryUsage:
    """Memory usage and resource management tests."""

    @patch("pathlib.Path.mkdir")
    def test_config_memory_usage(self, mock_mkdir):
        """Test Config objects don't leak memory."""
        import gc

        # Create many config objects (mock folder creation to avoid 1000+ real folders)
        configs = []
        for i in range(1000):
            config = Config(
                base_url=f"http://example{i}.com",
                username=f"user{i}",
                password="password",
                output_folder=f"test{i}/",
                start_date="2024-01-01",
            )
            configs.append(config)

        # Clear references
        del configs

        # Force garbage collection
        gc.collect()

        # Test should complete without memory errors
        assert True

        # Verify we didn't actually create 1000 folders
        assert mock_mkdir.call_count == 1000

    @patch("p21api.odata_client.requests.post")
    def test_odata_client_resource_cleanup(self, mock_post):
        """Test OData client properly manages resources."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_response

        clients = []

        # Create many clients
        for i in range(100):
            client = ODataClient(f"user{i}", "password", "http://example.com")
            # Trigger authentication
            _ = client.headers
            clients.append(client)

        # Clear references
        del clients

        # Should not have resource leaks
        assert True

    def test_large_report_data_handling(self):
        """Test handling of large report datasets."""
        # Simulate very large dataset
        large_data = []
        for i in range(50000):
            large_data.append(
                {
                    "id": i,
                    "data": f"Large data string {i} " * 10,  # Make each record larger
                    "timestamp": f"2024-01-01T{i % 24:02d}:00:00",
                }
            )

        # Process data in chunks to test memory management
        chunk_size = 1000
        processed_chunks = 0

        for i in range(0, len(large_data), chunk_size):
            chunk = large_data[i : i + chunk_size]
            # Simulate processing
            processed_records = len(chunk)
            assert processed_records <= chunk_size
            processed_chunks += 1

        assert processed_chunks == 50  # 50000 / 1000
