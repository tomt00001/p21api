import calendar
from datetime import datetime
from functools import cached_property

import requests


class ODataClient:
    def __init__(self, username: str, password: str, base_url: str) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url

    @cached_property
    def headers(self) -> dict:
        return self._get_headers()

    def _get_headers(self) -> dict:
        """Authenticate and get Bearer token."""
        url = f"{self.base_url}/api/security/token"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.post(
            url,
            headers={
                **headers,
                "username": self.username,
                "password": self.password,
            },
        )

        if response.status_code == 200:
            headers["Authorization"] = f"Bearer {response.json().get('AccessToken')}"
            return headers
        else:
            raise Exception(f"Failed to obtain token: {response.text}")

    def fetch_data(self, url: str) -> dict | None:
        """Fetch data from the given endpoint with date filters."""
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.text}\nUrl:{url}")
        data = response.json()

        value = data.get("value")
        if not value:
            return None
        return value

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
        start_date: "datetime | None" = None,
        **kwargs,
    ) -> str:
        filter_params = []

        url = self._get_endpoint_url(endpoint)

        url_params = []
        url_params.append(self._get_selects(selects))

        if start_date:
            filter_params = self._get_startdate_filter(start_date) or []

        filters = kwargs.get("filters")
        if filters:
            filter_params.extend(filters)
        url_params.append(self._get_filters(filter_params))

        order_by = kwargs.get("order_by")
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
        **kwargs,
    ) -> tuple[dict | None, str]:
        url = self.compose_url(
            endpoint=endpoint,
            start_date=start_date,
            **kwargs,
        )

        return self.fetch_data(url), url

    def post_odataservice(
        self,
        endpoint: str,
        selects: list[str],
        start_date: datetime | None = None,
        page_size: int = 1000,
        **kwargs,
    ) -> dict | None:
        body = {}
        url = self._get_endpoint_url(endpoint)

        url = self.compose_url(
            endpoint=endpoint,
            selects=selects,
            start_date=start_date,
            **kwargs,
        )
        url = f"{url}&$count=true&$top={page_size}"

        max_count = 0
        count = 0
        data = []
        while True:
            response = requests.post(
                f"{url}&$skip={count}",
                headers=self.headers,
                json=body,
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
