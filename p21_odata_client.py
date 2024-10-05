import calendar
from datetime import datetime

import requests


class P21ODataClient:
    def __init__(
        self, base_url: str, username: str, password: str, *args, **kwargs
    ) -> None:
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.token = self.get_bearer_token(username, password)

        if "debug" in kwargs:
            self.debug = bool(kwargs.get("debug"))

    def get_bearer_token(self, username: str, password: str) -> str:
        """Authenticate and get Bearer token."""
        url = f"{self.base_url}/api/security/token"

        response = requests.post(
            url,
            headers={
                **self.headers,
                "username": username,
                "password": password,
            },
        )

        if response.status_code == 200:
            return response.json().get("AccessToken")
        else:
            raise Exception(f"Failed to obtain token: {response.text}")

    def fetch_data(self, url: str) -> dict:
        """Fetch data from the given endpoint with date filters."""
        headers = {
            **self.headers,
            "Authorization": f"Bearer {self.token}",
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.text}")
        data = response.json()

        value = data.get("value")
        if not value:
            raise ValueError(
                "Value key not found in data response. \
                            This is an error"
            )
        return value

    def compose_url(
        self,
        endpoint: str,
        api: str,
        start_date: "datetime | None" = None,
        **kwargs,
    ) -> str:
        filter_params = []

        url = f"{self.base_url}"
        if api == "data":
            url += "/data/erp/views/v1/"
        elif api == "odataservice":
            url += "/odataservice/odata/view/"
        url += f"{endpoint}"

        url_params = []

        # list of fields to select from the endpoint
        selects = kwargs.get("selects")
        if not selects:
            raise ValueError("selects is required")
        else:
            url_params.append(f"$select={','.join(selects)}")

        # Datetime filters can be None.  If None, that kwargs filters is
        # required to be populated with a filter
        if start_date_datetime := start_date:
            end_date_time = kwargs.get("end_date") or self.get_current_month_end_date(
                start_date_datetime
            )
            filter_params = self.get_datetime_filter(
                "date_created", start_date_datetime, end_date_time, api
            )

        filters = kwargs.get("filters")
        if self.debug:
            print(f"type: {type(filters)} filters: {filters}")
        if not start_date and not filters:
            raise ValueError(
                "Either start_date or filters must be provided. \
                            Both cannot be None"
            )
        if filters:
            filter_params.extend(filters)
        if filter_params:
            url_params.append(f"$filter={' and '.join(filter_params)}")

        order_by = kwargs.get("order_by")
        if order_by:
            url_params.append(f"$orderby={','.join(order_by)}")

        final_url = f"{url}?{'&'.join(url_params)}"
        if self.debug:
            print(f"url: {final_url}")
        return final_url

    def get_datetime_filter(
        self,
        field: str,
        start_date: datetime,
        end_date: datetime,
        api: str,
    ) -> list[str]:
        str_start_date = self._datetime_to_str(start_date)
        str_end_date = self._datetime_to_str(end_date)
        if api == "data":
            return [
                f"{field} ge datetime'{str_start_date}'",
                f"{field} le datetime'{str_end_date}'",
            ]
        elif api == "odataservice":
            return [
                f"{field} ge {str_start_date}",
                f"{field} le {str_end_date}",
            ]
        else:
            raise ValueError("Invalid API type")

    def _datetime_to_str(self, input_datetime: datetime) -> str:
        return input_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_current_month_end_date(
        self,
        input_datetime: datetime,
    ) -> datetime:
        last_day_of_month = calendar.monthrange(
            input_datetime.year, input_datetime.month
        )[1]
        return input_datetime.replace(day=last_day_of_month)

    def query_data(
        self,
        endpoint: str,
        start_date: datetime | None = None,
        **kwargs,
    ) -> tuple[dict, str]:
        url = self.compose_url(
            endpoint=endpoint,
            api="data",
            start_date=start_date,
            **kwargs,
        )

        return self.fetch_data(url), url

    def query_odataservice(
        self,
        endpoint: str,
        start_date: datetime | None = None,
        **kwargs,
    ) -> tuple[dict, str]:
        url = self.compose_url(
            endpoint=endpoint,
            api="odataservice",
            start_date=start_date,
            **kwargs,
        )

        return self.fetch_data(url), url
