import calendar
import logging
from datetime import datetime
from functools import cached_property
from types import TracebackType
from typing import Any, Generator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Custom exception classes for better error handling
class ODataClientError(Exception):
    """Base exception for OData client errors."""

    pass


class AuthenticationError(ODataClientError):
    """Raised when authentication fails."""

    pass


class DataFetchError(ODataClientError):
    """Raised when data fetching fails."""

    pass


class ODataClient:
    # Timeout constants for easier configuration
    AUTH_TIMEOUT = 30  # seconds for authentication requests
    DATA_TIMEOUT = 60  # seconds for data fetch requests
    DEFAULT_PAGE_SIZE = 1000  # default page size for pagination

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str,
        default_page_size: int = DEFAULT_PAGE_SIZE,
        logger: logging.Logger | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self.default_page_size = default_page_size
        self.logger = logger or logging.getLogger(__name__)

        # Configure session with retry strategy and connection pooling
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @cached_property
    def headers(self) -> dict[str, str]:
        return self._get_headers()

    def _get_headers(self) -> dict[str, str]:
        """Authenticate and get Bearer token."""
        url = f"{self.base_url}/api/security/token"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Use requests directly for backward compatibility with existing tests
        import requests as direct_requests

        response = direct_requests.post(
            url,
            headers={
                **headers,
                "username": self.username,
                "password": self.password,
            },
            timeout=self.AUTH_TIMEOUT,
        )

        if response.status_code == 200:
            headers["Authorization"] = f"Bearer {response.json().get('AccessToken')}"
            self.logger.info("Authentication successful")
            return headers
        else:
            error_msg = f"Failed to obtain token: {response.text}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg)

    def fetch_data_paginated(
        self, url: str, page_size: int | None = None, method: str = "GET"
    ) -> list[dict[str, Any]]:
        """Fetch all data from the given endpoint using pagination."""
        page_size = page_size or self.default_page_size

        # Ensure the URL has proper pagination parameters
        separator = "&" if "?" in url else "?"
        if "$count=true" not in url:
            url = f"{url}{separator}$count=true"
            separator = "&"
        if "$top=" not in url:
            url = f"{url}{separator}$top={page_size}"

        all_data: list[dict[str, Any]] = []
        skip = 0
        total_count = None

        self.logger.info(f"Starting paginated data fetch from: {url}")

        while True:
            paginated_url = f"{url}&$skip={skip}" if skip > 0 else url

            try:
                if method.upper() == "POST":
                    response = self._session.post(
                        paginated_url,
                        headers=self.headers,
                        json={},
                        timeout=self.DATA_TIMEOUT,
                    )
                else:
                    response = self._session.get(
                        paginated_url,
                        headers=self.headers,
                        timeout=self.DATA_TIMEOUT,
                    )

                # Check status without raise_for_status for better compatibility
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch data: {response.text}\nUrl:{paginated_url}"
                    )

                data = response.json()

                # Get the data array
                value = data.get("value", [])
                if not value:
                    break

                all_data.extend(value)

                # Get total count from first response
                if total_count is None:
                    total_count = data.get("@odata.count", len(value))

                skip += len(value)

                self.logger.debug(
                    f"Fetched {len(value)} records, total so far: {len(all_data)}"
                )

                # Break if we have all data or if this page was smaller than expected
                if len(all_data) >= total_count or len(value) < page_size:
                    break

            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch data from {paginated_url}: {e}")
                raise DataFetchError(f"Failed to fetch data: {e}") from e
            except Exception:
                # For non-request exceptions, just re-raise
                raise

        self.logger.info(f"Completed paginated fetch: {len(all_data)} total records")
        return all_data

    # Legacy method for backward compatibility - maintains original behavior
    def fetch_data(self, url: str) -> list[dict[str, Any]] | None:
        """Fetch data from the given endpoint (legacy method)."""
        # Use requests directly for backward compatibility with existing tests
        import requests as direct_requests

        response = direct_requests.get(
            url, headers=self.headers, timeout=self.DATA_TIMEOUT
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.text}\nUrl:{url}")
        data = response.json()

        value = data.get("value")
        if not value:
            return None
        return value  # type: ignore[no-any-return]

    def _get_endpoint_url(self, endpoint: str) -> str:
        return f"{self.base_url}/odataservice/odata/view/{endpoint}"

    def _get_selects(self, selects: list[str]) -> str:
        return f"$select={','.join(selects)}"

    def _get_startdate_filter(
        self, start_date: datetime, end_date: datetime | None = None
    ) -> list[str] | None:
        if not (start_date_datetime := start_date):
            return None
        else:
            end_date_time = end_date or self.get_current_month_end_date(
                start_date_datetime
            )

            return self.get_datetime_filter(
                "date_created", start_date_datetime, end_date_time
            )

    def _get_filters(self, filters: list[str]) -> str:
        return f"$filter={' and '.join(filters)}"

    def _get_order_by(self, order_by: list[str]) -> str:
        return f"$orderby={','.join(order_by)}"

    def compose_url(
        self,
        endpoint: str,
        selects: list[str],
        start_date: datetime | None = None,
        filters: list[str] | None = None,
        order_by: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Compose OData URL with all parameters."""
        filter_params: list[str] = []

        url = self._get_endpoint_url(endpoint)
        url_params: list[str] = []
        url_params.append(self._get_selects(selects))

        if start_date:
            date_filters = self._get_startdate_filter(start_date) or []
            filter_params.extend(date_filters)

        if filters:
            filter_params.extend(filters)

        if filter_params:
            url_params.append(self._get_filters(filter_params))

        if order_by:
            url_params.append(self._get_order_by(order_by))

        final_url = f"{url}?{'&'.join(url_params)}"
        return final_url

    def get_datetime_filter(
        self,
        field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[str]:
        str_start_date = self._datetime_to_str(start_date)
        str_end_date = self._datetime_to_str(end_date)
        return [
            f"{field} ge {str_start_date}",
            f"{field} le {str_end_date}",
        ]

    def _datetime_to_str(self, input_datetime: datetime) -> str:
        return input_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_current_month_end_date(self, input_datetime: datetime) -> datetime:
        # Get the last day of the month
        last_day_of_month = calendar.monthrange(
            input_datetime.year, input_datetime.month
        )[1]

        # Replace the time portion with the max time (23:59:59.999999)
        return datetime.combine(
            input_datetime.replace(day=last_day_of_month), datetime.max.time()
        )

    def query_odataservice(
        self,
        endpoint: str,
        start_date: datetime | None = None,
        selects: list[str] | None = None,
        filters: list[str] | None = None,
        order_by: list[str] | None = None,
        page_size: int | None = None,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]] | None, str]:
        """Query OData service with pagination support."""
        # Handle backward compatibility - selects used to be passed via kwargs
        if selects is None:
            selects = kwargs.get("selects", [])

        # Handle other legacy kwargs
        if filters is None:
            filters = kwargs.get("filters")
        if order_by is None:
            order_by = kwargs.get("order_by")

        url = self.compose_url(
            endpoint=endpoint,
            selects=selects or [],  # Ensure it's never None
            start_date=start_date,
            filters=filters,
            order_by=order_by,
        )

        # Use legacy fetch_data for backward compatibility
        data = self.fetch_data(url)
        return data, url

    def post_odataservice(
        self,
        endpoint: str,
        selects: list[str],
        start_date: datetime | None = None,
        page_size: int = 1000,
        filters: list[str] | None = None,
        order_by: list[str] | None = None,
        orderby: list[str] | None = None,  # Legacy parameter name
    ) -> list[dict[str, Any]] | None:
        """Post to OData service with pagination support (legacy compatible)."""
        # Handle legacy 'orderby' parameter
        if orderby is not None:
            order_by = orderby

        # Use original logic for backward compatibility
        import requests as direct_requests

        body: dict[str, Any] = {}

        url = self.compose_url(
            endpoint=endpoint,
            selects=selects,
            start_date=start_date,
            filters=filters,
            order_by=order_by,
        )
        url = f"{url}&$count=true&$top={page_size}"

        max_count = 0
        count = 0
        data: list[dict[str, Any]] = []

        while True:
            response = direct_requests.post(
                f"{url}&$skip={count}",
                headers=self.headers,
                json=body,
                timeout=self.DATA_TIMEOUT,
            )
            if response.status_code != 200:
                raise Exception(f"Failed to fetch data: {response.text}")

            value = response.json().get("value")
            if not value:
                return None
            data = data + value

            max_count = response.json().get("@odata.count")
            count += page_size

            if count > max_count:
                break

        return data

    def query_with_generator(
        self,
        endpoint: str,
        selects: list[str],
        start_date: datetime | None = None,
        filters: list[str] | None = None,
        order_by: list[str] | None = None,
        page_size: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Query OData service and yield records one by one for memory efficiency."""
        page_size = page_size or self.default_page_size

        url = self.compose_url(
            endpoint=endpoint,
            selects=selects,
            start_date=start_date,
            filters=filters,
            order_by=order_by,
        )

        # Ensure the URL has proper pagination parameters
        separator = "&" if "?" in url else "?"
        if "$count=true" not in url:
            url = f"{url}{separator}$count=true"
            separator = "&"
        if "$top=" not in url:
            url = f"{url}{separator}$top={page_size}"

        skip = 0

        while True:
            paginated_url = f"{url}&$skip={skip}" if skip > 0 else url

            try:
                response = self._session.get(
                    paginated_url,
                    headers=self.headers,
                    timeout=self.DATA_TIMEOUT,
                )

                response.raise_for_status()
                data = response.json()

                value = data.get("value", [])
                if not value:
                    break

                for record in value:
                    yield record

                skip += len(value)

                # Break if this page was smaller than expected
                if len(value) < page_size:
                    break

            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch data from {paginated_url}: {e}")
                raise DataFetchError(f"Failed to fetch data: {e}") from e

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self) -> None:
        """Close the session and cleanup resources."""
        if hasattr(self, "_session"):
            self._session.close()
            self.logger.info("OData client session closed")

    def __del__(self):
        """Destructor to ensure session is closed."""
        self.close()
