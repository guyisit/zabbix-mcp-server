#!/usr/bin/env python3
"""
Zabbix MCP Server - Unified API interface using python-zabbix-utils

This server provides complete access to ALL Zabbix API functionality through
a single unified tool, enabling AI assistants to interact with Zabbix monitoring
systems dynamically.

Author: Zabbix MCP Server Contributors
License: MIT
"""

import os
import logging
from typing import Any, Dict, Optional
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .client import get_zabbix_client
from .utils import is_read_only, is_read_operation, format_response

logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG") else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("Zabbix MCP Server")


@mcp.tool()
def zabbix_api(method: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Execute any Zabbix API method dynamically.

    This unified tool provides access to ALL Zabbix API functionality through
    a single interface. The method parameter follows the format 'object.action'
    (e.g., 'host.get', 'item.create', 'trigger.update').

    IMPORTANT - Output Parameter Best Practices:
    For 'get' operations, ALWAYS specify the 'output' parameter explicitly
    to improve performance and reduce response size.

    ✅ RECOMMENDED: Specify only needed fields
    params={'output': ['hostid', 'name', 'status']}

    ❌ DISCOURAGED: Using 'extend' (returns ALL fields, slow and verbose)
    params={'output': 'extend'}

    📋 DEFAULT: If 'output' is not specified, defaults to ['name']
    This provides minimal but useful information for most use cases.

    Args:
        method: Zabbix API method in format 'object.action'
        Examples: 'host.get', 'item.create', 'trigger.update',
        'problem.get', 'template.create', 'user.get'

        params: Dictionary of parameters for the API method (optional)
        Examples:
        {'output': ['hostid', 'name']} - Specific fields (RECOMMENDED)
        {'output': 'extend'} - All fields (DISCOURAGED, slow)
        {'hostids': ['10084'], 'output': ['itemid', 'name', 'lastvalue']}

    Returns:
        str: JSON formatted response from Zabbix API

    Examples:
    # Get hosts with specific fields (RECOMMENDED)
    >>> zabbix_api(method='host.get', params={'output': ['hostid', 'name', 'status']})

    # Get hosts in a specific group with limited fields
    >>> zabbix_api(method='host.get', params={
    ... 'groupids': ['1'],
    ... 'output': ['hostid', 'name']
    ... })

    # Get items for a host with specific fields (RECOMMENDED)
    >>> zabbix_api(method='item.get', params={
    ... 'hostids': ['10084'],
    ... 'output': ['itemid', 'name', 'lastvalue', 'units']
    ... })

    # Create a new host
    >>> zabbix_api(
    ... method='host.create',
    ... params={
    ... 'host': 'server-01',
    ... 'groups': [{'groupid': '1'}],
    ... 'interfaces': [{'type': 1, 'main': 1, 'useip': 1, 'ip': '192.168.1.100'}]
    ... }
    ... )

    # Get recent problems with specific fields (RECOMMENDED)
    >>> zabbix_api(method='problem.get', params={
    ... 'output': ['eventid', 'name', 'severity', 'clock'],
    ... 'recent': True,
    ... 'sortfield': 'clock',
    ... 'sortorder': 'DESC'
    ... })

    # Get API version (no params needed)
    >>> zabbix_api(method='apiinfo.version')

    Available Zabbix API Objects:
    - Host management: host, hostgroup, template
    - Monitoring: item, trigger, graph, discoveryrule, itemprototype
    - Data: history, trend, problem, event
    - Users: user, usergroup, usermacro
    - Infrastructure: proxy, maintenance
    - Configuration: configuration, action, alert
    - Discovery: dhost, dservice, drule, dcheck
    - And many more - see Zabbix API documentation

    Raises:
        ValueError: If server is in read-only mode and method is a write operation
        ValueError: If method format is invalid
        Exception: If Zabbix API returns an error

    Performance Tips:
    - Always specify 'output' with only needed fields
    - Use 'limit' parameter to restrict number of results
    - Use 'filter' parameter to reduce data transfer
    - Avoid 'output: extend' for large datasets

    Note:
    For full Zabbix API documentation, visit:
    https://www.zabbix.com/documentation/current/manual/api/reference
    """
    if is_read_only() and not is_read_operation(method):
        raise ValueError(
            f"Server is in read-only mode - operation '{method}' is not allowed. "
            f"Only safe read operations (get, version, check, export) are permitted. "
            f"Write operations (create, update, delete) are blocked."
        )

    client = get_zabbix_client()

    if params is None:
        params = {}

    if method.endswith(".get") and "output" not in params:
        params = {**params, "output": ["name"]}
        logger.debug(f"Applied default output=['name'] for {method}")

    parts = method.split(".")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid method format: '{method}'. "
            f"Expected format: 'object.action' (e.g., 'host.get', 'item.create')"
        )

    api_object, api_action = parts

    api_obj = getattr(client, api_object)
    api_method = getattr(api_obj, api_action)

    try:
        if params:
            result = api_method(**params)
        else:
            result = api_method()

        logger.info(f"Successfully executed {method}")
        return format_response(result)

    except Exception as e:
        logger.error(f"Error executing {method}: {e}")
        raise


def get_transport_config() -> Dict[str, Any]:
    transport = os.getenv("ZABBIX_MCP_TRANSPORT", "stdio").lower()

    if transport not in ["stdio", "streamable-http"]:
        raise ValueError(
            f"Invalid ZABBIX_MCP_TRANSPORT: {transport}. "
            f"Must be 'stdio' or 'streamable-http'"
        )

    config = {"transport": transport}

    if transport == "streamable-http":
        auth_type = os.getenv("AUTH_TYPE", "").lower()
        if auth_type != "no-auth":
            raise ValueError(
                "AUTH_TYPE must be set to 'no-auth' when using streamable-http transport"
            )

        config.update(
            {
                "host": os.getenv("ZABBIX_MCP_HOST", "127.0.0.1"),
                "port": int(os.getenv("ZABBIX_MCP_PORT", "8000")),
                "stateless_http": os.getenv(
                    "ZABBIX_MCP_STATELESS_HTTP", "false"
                ).lower()
                in ("true", "1", "yes"),
            }
        )

        logger.info(
            f"HTTP transport configured: {config['host']}:{config['port']}, "
            f"stateless_http={config['stateless_http']}"
        )

    return config


def main():
    logger.info("Starting Zabbix MCP Server")

    try:
        transport_config = get_transport_config()
        logger.info(f"Transport: {transport_config['transport']}")
    except ValueError as e:
        logger.error(f"Transport configuration error: {e}")
        return 1

    logger.info(f"Read-only mode: {is_read_only()}")
    logger.info(f"Zabbix URL: {os.getenv('ZABBIX_URL', 'Not configured')}")

    try:
        if transport_config["transport"] == "stdio":
            mcp.run()
        else:
            mcp.run(
                transport="streamable-http",
                host=transport_config["host"],
                port=transport_config["port"],
                stateless_http=transport_config["stateless_http"],
            )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    main()
