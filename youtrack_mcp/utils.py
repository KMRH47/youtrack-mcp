"""
Utility functions for YouTrack MCP server.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

from youtrack_mcp.config import config


def convert_timestamp_to_iso8601(timestamp_ms: int) -> str:
    """
    Convert YouTrack epoch timestamp (in milliseconds) to ISO8601 format in UTC.

    Args:
        timestamp_ms: Timestamp in milliseconds since Unix epoch

    Returns:
        ISO8601 formatted timestamp string in UTC timezone
    """
    try:
        # Convert milliseconds to seconds
        timestamp_seconds = timestamp_ms / 1000
        # Create datetime object in UTC and format as ISO8601
        dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, OSError, OverflowError):
        # Return original timestamp as string if conversion fails
        return str(timestamp_ms)


def add_iso8601_timestamps(
    data: Union[Dict, List, Any],
) -> Union[Dict, List, Any]:
    """
    Recursively add ISO8601 formatted timestamps to YouTrack data.

    This function looks for timestamp fields (created, updated) that contain
    epoch timestamps in milliseconds and adds corresponding ISO8601 fields.

    Args:
        data: The data structure to process (dict, list, or other)

    Returns:
        The data structure with ISO8601 timestamps added
    """
    if isinstance(data, dict):
        # Create a copy to avoid modifying the original
        result = data.copy()

        # Process timestamp fields
        timestamp_fields = ["created", "updated"]
        for field in timestamp_fields:
            if field in result and isinstance(result[field], int):
                iso_field = f"{field}_iso8601"
                result[iso_field] = convert_timestamp_to_iso8601(result[field])

        # Recursively process nested dictionaries and lists
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                result[key] = add_iso8601_timestamps(value)

        return result

    elif isinstance(data, list):
        # Process each item in the list
        return [add_iso8601_timestamps(item) for item in data]

    else:
        # Return unchanged for other types
        return data


def format_json_response(data: Any) -> str:
    """
    Format data as JSON string with ISO8601 timestamps added.

    Args:
        data: The data to format

    Returns:
        JSON string with ISO8601 timestamps added
    """
    # Add ISO8601 timestamps to the data
    enhanced_data = add_iso8601_timestamps(data)

    # Return formatted JSON
    return json.dumps(enhanced_data, indent=2)


def normalize_issue_id(issue_id: str) -> str:
    """
    Normalize an issue ID by adding the default project key if it's just a number.

    Args:
        issue_id: The issue ID to normalize (e.g., "123" or "AGI-123")

    Returns:
        Normalized issue ID (e.g., "AGI-123")
    """
    if not issue_id:
        return issue_id

    # If it's already in the correct format (contains a dash), return as-is
    if '-' in issue_id:
        return issue_id

    # If it's just a number and we have a default project key, prepend it
    if re.match(r'^\d+$', issue_id) and config.DEFAULT_PROJECT_KEY:
        return f"{config.DEFAULT_PROJECT_KEY}-{issue_id}"

    # Otherwise, return as-is
    return issue_id


def normalize_query_parameter(query: str) -> str:
    """
    Normalize a query parameter by adding the default project key to bare issue numbers.

    Args:
        query: The query string that might contain bare issue numbers

    Returns:
        Normalized query string
    """
    if not query or not config.DEFAULT_PROJECT_KEY:
        return query

    # Look for standalone numbers that could be issue IDs
    # Match numbers that are:
    # - At start of string followed by space/end
    # - After space followed by space/end
    # - The entire string
    def replace_bare_numbers(match):
        number = match.group(1)
        return f"{config.DEFAULT_PROJECT_KEY}-{number}"

    # Replace bare numbers with project-prefixed versions
    # This regex matches numbers that are likely issue IDs
    normalized = re.sub(r'\b(\d{3,})\b', replace_bare_numbers, query)

    return normalized
