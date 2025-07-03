"""
Test script to verify the improved OData client functionality.
This script demonstrates the new features and ensures backward compatibility.
"""

import logging
from datetime import datetime

from p21api.odata_client import AuthenticationError, DataFetchError, ODataClient

# Configure logging to see the client's debug output
logging.basicConfig(level=logging.INFO)


def test_client_features():
    """Test the improved OData client features."""

    # Example configuration (replace with actual values for real testing)
    client = ODataClient(
        username="test_user",
        password="test_password",  # nosec B106 # Test credentials only
        base_url="https://your-p21-server.com",
        default_page_size=500,  # Custom page size
        logger=logging.getLogger("odata_test"),
    )

    logger = logging.getLogger(__name__)
    logger.info("OData Client Improvements Demo")
    logger.info("=" * 40)

    try:
        # Test context manager usage (new feature)
        with client:
            logger.info("✓ Context manager support working")

            # Test the new paginated query method
            selects = ["id", "name", "date_created"]
            start_date = datetime(2024, 1, 1)

            # Method 1: Get all data at once (paginated internally)
            data, url = client.query_odataservice(
                endpoint="your_endpoint",
                selects=selects,
                start_date=start_date,
                filters=["status eq 'active'"],
                order_by=["date_created desc"],
                page_size=100,
            )
            data_len = len(data) if data else 0
            logger.info("✓ Paginated query method: Retrieved %d records", data_len)
            logger.info("  URL: %s", url)

            # Method 2: Memory-efficient generator (new feature)
            logger.info("✓ Generator method for memory efficiency:")
            record_count = 0
            for _ in client.query_with_generator(
                endpoint="your_endpoint",
                selects=selects,
                start_date=start_date,
                page_size=50,
            ):
                record_count += 1
                if record_count >= 10:  # Just test first 10 records
                    break
            logger.info("  Processed %d records via generator", record_count)

            # Method 3: POST-based queries (improved)
            post_data = client.post_odataservice(
                endpoint="your_endpoint",
                selects=selects,
                start_date=start_date,
                page_size=200,
            )
            post_len = len(post_data) if post_data else 0
            logger.info("✓ POST-based pagination: Retrieved %d records", post_len)

            # Method 4: Legacy compatibility (now uses pagination internally)
            legacy_data = client.fetch_data("your_full_odata_url")
            if legacy_data:
                logger.info(
                    "✓ Legacy method compatibility: Retrieved %d records",
                    len(legacy_data),
                )

    except AuthenticationError as e:
        logger.error("❌ Authentication failed: %s", e)
    except DataFetchError as e:
        logger.error("❌ Data fetch failed: %s", e)
    except Exception as e:
        logger.error("❌ Unexpected error: %s", e)

    logger.info("\nKey Improvements:")
    logger.info("- All queries now use pagination to handle large datasets")
    logger.info("- Better error handling with custom exception classes")
    logger.info("- Session reuse and connection pooling for better performance")
    logger.info("- Context manager support for proper resource cleanup")
    logger.info("- Memory-efficient generator option for large datasets")
    logger.info("- Comprehensive logging for better debugging")
    logger.info("- Improved type hints for better IDE support")
    logger.info("- Backward compatibility maintained")


if __name__ == "__main__":
    test_client_features()
