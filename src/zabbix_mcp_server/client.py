#!/usr/bin/env python3

import os
import logging
from typing import Optional
from zabbix_utils import ZabbixAPI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG") else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

zabbix_api_client: Optional[ZabbixAPI] = None


def get_zabbix_client() -> ZabbixAPI:
    global zabbix_api_client

    if zabbix_api_client is None:
        url = os.getenv("ZABBIX_URL")
        if not url:
            raise ValueError("ZABBIX_URL environment variable is required")

        logger.info(f"Initializing Zabbix API client for {url}")

        verify_ssl = os.getenv("VERIFY_SSL", "true").lower() in ("true", "1", "yes")
        logger.info(
            f"SSL certificate verification: {'enabled' if verify_ssl else 'disabled'}"
        )

        skip_version_check = os.getenv(
            "ZABBIX_SKIP_VERSION_CHECK", "false"
        ).lower() in ("true", "1", "yes")
        if skip_version_check:
            logger.info("Skipping Zabbix API version check")

        zabbix_api_client = ZabbixAPI(
            url=url, validate_certs=verify_ssl, skip_version_check=skip_version_check
        )

        token = os.getenv("ZABBIX_TOKEN")
        if token:
            logger.info("Authenticating with API token")
            zabbix_api_client.login(token=token)
        else:
            user = os.getenv("ZABBIX_USER")
            password = os.getenv("ZABBIX_PASSWORD")
            if not user or not password:
                raise ValueError(
                    "Either ZABBIX_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD must be set"
                )
            logger.info(f"Authenticating with username: {user}")
            zabbix_api_client.login(user=user, password=password)

        logger.info("Successfully authenticated with Zabbix API")

    return zabbix_api_client
