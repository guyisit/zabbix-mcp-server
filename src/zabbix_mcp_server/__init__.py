"""
Zabbix MCP Server

A comprehensive Model Context Protocol (MCP) server for Zabbix integration.
"""

__version__ = "2.0.0"
__author__ = "mpeirone"
__license__ = "MIT"

from zabbix_mcp_server.server import (
    get_zabbix_client,
    is_read_operation,
    is_read_only,
    get_transport_config,
    main,
    mcp,
)

__all__ = [
    "get_zabbix_client",
    "is_read_operation",
    "is_read_only",
    "get_transport_config",
    "main",
    "mcp",
]
