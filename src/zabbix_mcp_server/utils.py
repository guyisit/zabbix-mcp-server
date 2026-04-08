#!/usr/bin/env python3

import os
import json
from typing import Any


def is_read_only() -> bool:
    return os.getenv("READ_ONLY", "true").lower() in ("true", "1", "yes")


def is_read_operation(method: str) -> bool:
    if "." not in method:
        return False

    operation = method.split(".")[-1].lower()
    read_operations = {"get", "version", "check", "export"}

    return operation in read_operations


def format_response(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)
