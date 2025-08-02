"""
Fetch and save the OData $metadata XML schema for the configured service.
Usage:
    uv run python fetch_odata_metadata.py

This script authenticates using the configured environment (env/env.prod),
fetches the OData $metadata, and saves it to odata_schema/odata_metadata.xml.
"""

import logging
from pathlib import Path

import defusedxml.ElementTree as ET
from p21api.config import Config
from p21api.odata_client import ODataClient


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    config = Config()
    output_dir = Path(__file__).parent / "odata_schema"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "odata_metadata.xml"
    with ODataClient(
        username=config.username,  # type: ignore[arg-type]
        password=config.password,  # type: ignore[arg-type]
        base_url=config.base_url,
        logger=logging.getLogger("fetch_odata_metadata"),
    ) as client:
        import requests as direct_requests

        # --- P21 OData $metadata fetch logic ---
        # Primary/known working endpoint for Epicor P21:
        primary_path = "/data/erp/views/v1/$metadata"
        primary_url = f"{config.base_url.rstrip('/')}{primary_path}"
        header_set = dict(client.headers)
        header_set["Accept"] = "application/xml"
        logging.info(
            f"Trying primary $metadata endpoint: {primary_url} "
            f"with Accept: application/xml"
        )
        try:
            response = direct_requests.get(
                primary_url,
                headers=header_set,
                timeout=client.DATA_TIMEOUT,
            )
            if response.status_code == 200:
                metadata_xml = response.text
                output_file.write_text(metadata_xml, encoding="utf-8")
                msg = (
                    f"SUCCESS: OData $metadata saved to: {output_file} "
                    f"(endpoint: {primary_url}, Accept: application/xml)"
                )
                logging.info(msg)
                # print(msg)  # Removed for lint compliance
                odata_version = (
                    response.headers.get("OData-Version")
                    or response.headers.get("dataserviceversion")
                    or response.headers.get("OData-MaxVersion")
                )
                if odata_version:
                    logging.info(f"OData version (from headers): {odata_version}")
                    # print(f"OData version (from headers): {odata_version}")
                else:
                    logging.warning("OData version not found in HTTP headers.")
                    # print("OData version not found in HTTP headers.")
                try:
                    root = ET.fromstring(metadata_xml)
                    edmx_ns = root.tag.split("}")[0].strip("{")
                    version_attr = root.attrib.get("Version")
                    logging.info(
                        f"$metadata root tag: {root.tag}, namespace: {edmx_ns}, "
                        f"Version attribute: {version_attr}"
                    )
                    # print(
                    #     f"$metadata root tag: {root.tag}, namespace: {edmx_ns}, "
                    #     f"Version attribute: {version_attr}"
                    # )
                except Exception as ex:
                    logging.warning(f"Could not parse $metadata XML root: {ex}")
                    # print(f"Could not parse $metadata XML root: {ex}")
                return
            else:
                msg = (
                    f"FAILED: {primary_url} (Accept: application/xml) -> "
                    f"{response.status_code} {response.text[:200]}"
                )
                logging.warning(msg)
                # print(msg)
        except Exception as e:
            msg = f"EXCEPTION: {primary_url} (Accept: application/xml) -> {e}"
            logging.warning(msg)
            # print(msg)
        # Optionally, fallback to legacy multi-endpoint logic here if needed
        # print("ERROR: Primary $metadata endpoint failed. See logs above for details.")
        import sys

        sys.exit(1)


if __name__ == "__main__":
    main()
